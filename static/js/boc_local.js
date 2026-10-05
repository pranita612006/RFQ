/**
 * Costing Calculator: Local BOC (Bill of Components) Runtime Module
 * Handles dynamic row insertion with formatting/XSS protection
 * and AJAX batch persistence to backend API.
 */

// Utility: Escape HTML entities to prevent XSS injection
function escapeHtml(str) {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

// Utility: Safely parse floats with fallback to 0.0
function safeParseFloat(val, fallback = 0.0) {
  if (val === null || val === undefined || val === '') return fallback;
  const parsed = parseFloat(val);
  return isNaN(parsed) ? fallback : parsed;
}

// Utility: Retrieve Django CSRF token from cookies or DOM
function getCSRFToken() {
  const cookieMatch = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
  if (cookieMatch) return decodeURIComponent(cookieMatch[1]);
  const inputEl = document.querySelector('input[name="csrfmiddlewaretoken"]');
  if (inputEl) return inputEl.value;
  const metaEl = document.querySelector('meta[name="csrf-token"]');
  if (metaEl) return metaEl.getAttribute('content');
  return '';
}

/**
 * Function 1: addLocalBOCRow(dataObject)
 * - Checks and removes any .no-data-row element in #boc-local-bom-tbody.
 * - Safely formats values (parseFloat fallback to 0, .toFixed(2) for rate/price/cost).
 * - Escapes all string values against XSS vulnerabilities.
 * - Appends a dynamic <tr> with all lowercase field properties:
 *   (part_number, description, uom_code, quantity, internal_rate, settle_price, cost).
 * - Aligns numeric cells (quantity, internal_rate, settle_price, cost) to text-right.
 */
function addLocalBOCRow(dataObject = {}) {
  const tbody = document.getElementById('boc-local-bom-tbody');
  if (!tbody) {
    console.warn('[BOC] #boc-local-bom-tbody not found in DOM.');
    return null;
  }

  // 1. Remove any .no-data-row or empty placeholder rows
  const noDataRows = tbody.querySelectorAll('.no-data-row, .boc-empty-row');
  noDataRows.forEach(el => el.remove());

  // Also remove single full-width empty cell if present
  if (tbody.children.length === 1 && tbody.firstElementChild.cells.length <= 1) {
    tbody.firstElementChild.remove();
  }

  // 2. Safe parsing & numeric formatting
  const quantity = safeParseFloat(dataObject.quantity);
  const internalRate = safeParseFloat(
    dataObject.internal_rate !== undefined ? dataObject.internal_rate : dataObject.internal_cost
  );
  const settlePrice = safeParseFloat(dataObject.settle_price);
  const cost = safeParseFloat(
    dataObject.cost !== undefined ? dataObject.cost : (quantity * settlePrice)
  );

  // 3. String escaping against XSS
  const partNumber = escapeHtml(dataObject.part_number || '');
  const description = escapeHtml(dataObject.description || '');
  const uomCode = escapeHtml(dataObject.uom_code || dataObject.unit_of_measure_code || '');
  const rowId = dataObject.id ? escapeHtml(dataObject.id) : '';

  // 4. Construct dynamic <tr> with lowercase field properties
  const tr = document.createElement('tr');
  if (rowId) {
    tr.setAttribute('data-id', rowId);
    tr.setAttribute('data-row-id', rowId);
  }
  tr.setAttribute('data-type', 'local_boc');

  // Check if target table has a Cost header column
  const table = tbody.closest('#table-boc-local') || tbody.closest('table');
  const hasCostHeader = table && Array.from(table.querySelectorAll('thead th')).some(
    th => th.textContent.trim().toLowerCase().includes('cost')
  );

  const srNo = tbody.querySelectorAll('tr:not(.no-data-row)').length + 1;

  tr.innerHTML = `
    <td class="text-center col-srno">${srNo}</td>
    <td class="col-part-number">${partNumber}</td>
    <td class="col-description">${description}</td>
    <td class="col-uom-code">${uomCode}</td>
    <td class="text-right col-quantity col-qty">${quantity.toFixed(2)}</td>
    <td class="text-right col-internal-rate col-ir">${internalRate.toFixed(2)}</td>
    <td class="text-right col-settle-price col-sp">${settlePrice.toFixed(2)}</td>
    ${hasCostHeader ? `<td class="text-right col-cost">${cost.toFixed(2)}</td>` : ''}
    <td class="text-center"><button type="button" class="btn-edit-row" style="padding:2px 8px; font-size:12px; cursor:pointer; background:#2563eb; color:#fff; border:none; border-radius:4px;">Edit</button></td>
  `;

  tbody.appendChild(tr);
  return tr;
}

/**
 * Function 2: Save Event Listener on #btn-save-local-boc
 * - Reads all rows inside #boc-local-bom-tbody.
 * - Constructs JSON payload and executes Fetch POST to save_local_boc_data.
 * - Includes X-CSRFToken in request headers.
 */
function initLocalBOCSaveHandler() {
  const saveBtn = document.getElementById('btn-save-local-boc');
  if (!saveBtn) return;

  // Prevent multiple bindings
  if (saveBtn.dataset.bocListenerAttached === 'true') return;
  saveBtn.dataset.bocListenerAttached = 'true';

  saveBtn.addEventListener('click', async function (e) {
    e.preventDefault();

    const tbody = document.getElementById('boc-local-bom-tbody');
    if (!tbody) {
      alert('Local BOC table body (#boc-local-bom-tbody) not found.');
      return;
    }

    // Resolve customer_id and item_creation_id from top controls or container datasets
    const customerId =
      document.getElementById('top-customer-id')?.value?.trim() ||
      document.getElementById('boc-tab-root')?.dataset?.customerId ||
      new URLSearchParams(window.location.search).get('customer_id') ||
      '';

    const itemCreationId =
      document.getElementById('top-item-id')?.value?.trim() ||
      document.getElementById('boc-tab-root')?.dataset?.itemId ||
      new URLSearchParams(window.location.search).get('item_creation_id') ||
      '';

    if (!customerId || !itemCreationId) {
      alert('Please select both Customer ID and Item Creation ID before saving.');
      return;
    }

    // Read all rows inside #boc-local-bom-tbody
    const rows = [];
    const trElements = tbody.querySelectorAll('tr:not(.no-data-row):not(.boc-empty-row)');

    trElements.forEach(tr => {
      const cells = tr.children;
      if (cells.length < 6) return;

      const getCellTextOrInputValue = (cell) => {
        if (!cell) return '';
        const input = cell.querySelector('input, select, textarea');
        return (input ? input.value : cell.textContent).trim();
      };

      const rawId = tr.getAttribute('data-id') || tr.getAttribute('data-row-id');
      const rowId = rawId ? parseInt(rawId, 10) : null;

      const partNumber = getCellTextOrInputValue(cells[1]);
      const description = getCellTextOrInputValue(cells[2]);
      const uomCode = getCellTextOrInputValue(cells[3]);
      const quantity = safeParseFloat(getCellTextOrInputValue(cells[4]));
      const internalRate = safeParseFloat(getCellTextOrInputValue(cells[5]));
      const settlePrice = safeParseFloat(getCellTextOrInputValue(cells[6]));
      const cost = cells.length >= 8 
        ? safeParseFloat(getCellTextOrInputValue(cells[7]), quantity * settlePrice) 
        : (quantity * settlePrice);

      rows.push({
        id: isNaN(rowId) ? null : rowId,
        part_number: partNumber,
        description: description,
        uom_code: uomCode,
        unit_of_measure_code: uomCode,
        quantity: quantity,
        internal_rate: internalRate,
        internal_cost: internalRate,
        settle_price: settlePrice,
        cost: cost
      });
    });

    const payload = {
      customer_id: parseInt(customerId, 10) || customerId,
      item_creation_id: parseInt(itemCreationId, 10) || itemCreationId,
      rows: rows
    };

    saveBtn.disabled = true;
    const originalText = saveBtn.textContent;
    saveBtn.textContent = 'Saving...';

    try {
      const response = await fetch('/CostingBCCal/save-local-boc/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify(payload)
      });

      const responseText = await response.text();
      let result = {};
      try {
        result = JSON.parse(responseText);
      } catch (pErr) {
        throw new Error(`Server returned status ${response.status}`);
      }

      if (response.ok && result.status === 'success') {
        if (typeof showToast === 'function') {
          showToast(result.message || 'Local BOC records saved successfully.', 'success');
        } else {
          alert(result.message || 'Local BOC records saved successfully.');
        }

        // Reload table data if loadBOCTabData is available
        if (typeof window.loadBOCTabData === 'function') {
          await window.loadBOCTabData();
        }
      } else {
        const errorMsg = result.message || 'Failed to save Local BOC records.';
        if (typeof showToast === 'function') {
          showToast(errorMsg, 'error');
        } else {
          alert(errorMsg);
        }
      }
    } catch (err) {
      console.error('[BOC Save Error]', err);
      alert('Error saving Local BOC records: ' + err.message);
    } finally {
      saveBtn.disabled = false;
      saveBtn.textContent = originalText;
    }
  });
}

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initLocalBOCSaveHandler);
} else {
  initLocalBOCSaveHandler();
}

// Export functions to global scope for runtime modularity
window.addLocalBOCRow = addLocalBOCRow;
window.initLocalBOCSaveHandler = initLocalBOCSaveHandler;
window.escapeHtml = escapeHtml;
