/**
 * boc_calculations.js
 * Real-time calculation and DOM management logic for Bill of Costs (BOC) Tab.
 */

document.addEventListener('DOMContentLoaded', function () {
    initBocCalculations();
});

window.initBocCalculations = initBocCalculations;


/**
 * Main initialization function for BOC tab calculation event listeners.
 */
function initBocCalculations() {
    const rootEl = document.getElementById('boc-tab-root') || document;

    // 1. Real-time input listeners on editable quantity & rate fields
    rootEl.addEventListener('input', function (e) {
        if (
            e.target.classList.contains('boc-qty-input') || e.target.classList.contains('qty-input') ||
            e.target.classList.contains('boc-rate-input') || e.target.classList.contains('rate-input')
        ) {
            handleBomInputChange(e.target);
        } else if (e.target.id === 'boc-entry-rate' || e.target.id === 'boc-entry-qty') {
            updateDataEntryTotal();
        }
    });

    rootEl.addEventListener('change', function (e) {
        if (
            e.target.classList.contains('boc-qty-input') || e.target.classList.contains('qty-input') ||
            e.target.classList.contains('boc-rate-input') || e.target.classList.contains('rate-input')
        ) {
            handleBomInputChange(e.target);
        }
    });

    // 2. Add entry button click listener for "Data Entry : IMPORTED BOC"
    const addBtn = document.getElementById('btn-boc-add-entry');
    if (addBtn) {
        addBtn.addEventListener('click', handleAddImportedEntry);
    }

    // 3. Delegation for Overview row delete icon (✕!)
    rootEl.addEventListener('click', function (e) {
        if (e.target.classList.contains('boc-action-del')) {
            handleDeleteRow(e.target);
        }
    });

    // Initial calculation setup
    recalculateSubTotals();
}

/**
 * Auto-calculate Total Cost in Data Entry form: Total = Quantity * Rate
 */
function updateDataEntryTotal() {
    const rateInput = document.getElementById('boc-entry-rate');
    const qtyInput = document.getElementById('boc-entry-qty');
    const totalInput = document.getElementById('boc-entry-total');

    if (rateInput && qtyInput && totalInput) {
        const rate = parseFloat(rateInput.value) || 0;
        const qty = parseFloat(qtyInput.value) || 0;
        totalInput.value = (rate * qty).toFixed(2);
    }
}

/**
 * Handle input changes in Local/Imported BOM table inputs
 * Total_Cost = Quantity * RatePerUnit
 */
function handleBomInputChange(inputEl) {
    const row = inputEl.closest('tr');
    if (!row) return;

    const rowId = inputEl.getAttribute('data-row-id') || inputEl.getAttribute('data-id');
    const itemType = inputEl.getAttribute('data-type');

    const qtyInput = row.querySelector('.qty-input, .boc-qty-input');
    const rateInput = row.querySelector('.rate-input, .boc-rate-input');

    const qty = parseFloat(qtyInput ? qtyInput.value : 0) || 0;
    const rate = parseFloat(rateInput ? rateInput.value : 0) || 0;
    const totalCost = (qty * rate).toFixed(2);

    // Update Overview summary table row corresponding to this item
    const overviewTableId = itemType === 'local' ? 'boc-overview-local-tbody' : 'boc-overview-imported-tbody';
    const overviewTbody = document.getElementById(overviewTableId);

    if (overviewTbody) {
        let overviewRow = overviewTbody.querySelector(`tr[data-row-id="${rowId}"], tr[data-overview-id="${rowId}"]`);
        if (overviewRow) {
            const rateCell = overviewRow.querySelector('.rate-cell');
            const qtyCell = overviewRow.querySelector('.qty-cell');
            const totalCell = overviewRow.querySelector('.total-cell');

            if (rateCell) rateCell.textContent = rate.toFixed(4);
            if (qtyCell) qtyCell.textContent = qty.toFixed(2);
            if (totalCell) totalCell.textContent = totalCost;
        }
    }

    recalculateSubTotals();
}

/**
 * Recalculate Sub Totals for both Local and Imported Overview tables
 */
function recalculateSubTotals() {
    // Local Sub Total
    let localTotal = 0;
    const localRows = document.querySelectorAll('#boc-overview-local-tbody tr:not(.overview-empty-row)');
    localRows.forEach(row => {
        const totalCell = row.querySelector('.total-cell');
        if (totalCell) {
            localTotal += parseFloat(totalCell.textContent) || 0;
        }
    });
    const localSubtotalInput = document.getElementById('boc-local-subtotal');
    if (localSubtotalInput) {
        localSubtotalInput.value = localTotal.toFixed(2);
    }

    // Imported Sub Total
    let importedTotal = 0;
    const importedRows = document.querySelectorAll('#boc-overview-imported-tbody tr:not(.overview-empty-row)');
    importedRows.forEach(row => {
        const totalCell = row.querySelector('.total-cell');
        if (totalCell) {
            importedTotal += parseFloat(totalCell.textContent) || 0;
        }
    });
    const importedSubtotalInput = document.getElementById('boc-imported-subtotal');
    if (importedSubtotalInput) {
        importedSubtotalInput.value = importedTotal.toFixed(2);
    }
}

/**
 * Add new manual entry from Data Entry form to Overview table and backend
 */
function handleAddImportedEntry() {
    const descInput = document.getElementById('boc-entry-desc');
    const sizeInput = document.getElementById('boc-entry-tubesize');
    const unitInput = document.getElementById('boc-entry-unit');
    const rateInput = document.getElementById('boc-entry-rate');
    const qtyInput = document.getElementById('boc-entry-qty');
    const totalInput = document.getElementById('boc-entry-total');

    const desc = descInput ? descInput.value.trim() : '';
    const tubeSize = sizeInput ? sizeInput.value.trim() : '';
    const unit = unitInput ? unitInput.value.trim() : '';
    const rate = parseFloat(rateInput ? rateInput.value : 0) || 0;
    const qty = parseFloat(qtyInput ? qtyInput.value : 0) || 0;
    const totalCost = (rate * qty).toFixed(2);

    if (!desc) {
        alert('Please enter a description for the entry.');
        if (descInput) descInput.focus();
        return;
    }

    const rootEl = document.getElementById('boc-tab-root');
    const itemId = rootEl ? rootEl.getAttribute('data-item-id') : '';

    // Append to Overview Imported tbody
    const tbody = document.getElementById('boc-overview-imported-tbody');
    let tempId = 'new_' + Date.now();
    if (tbody) {
        // Remove empty placeholder row if present
        const emptyRow = tbody.querySelector('.overview-empty-row');
        if (emptyRow) emptyRow.remove();

        const tr = document.createElement('tr');
        tr.setAttribute('data-overview-id', tempId);
        tr.setAttribute('data-row-id', tempId);
        tr.setAttribute('data-type', 'manual_imported');

        tr.innerHTML = `
            <td>${escapeHtml(desc)}</td>
            <td>${escapeHtml(tubeSize)}</td>
            <td>${escapeHtml(unit)}</td>
            <td class="text-right rate-cell">${rate.toFixed(4)}</td>
            <td class="text-right qty-cell">${qty.toFixed(2)}</td>
            <td class="text-right total-cell">${totalCost}</td>
            <td class="text-center" style="border-right: none;">
                <button type="button" class="boc-action-del" data-id="${tempId}" data-type="manual_imported" title="Delete row">&times;!</button>
            </td>
        `;
        tbody.appendChild(tr);
    }

    // Persist via AJAX if item_creation_id is set
    if (itemId) {
        fetch('/CostingBCCal/boc/add-entry/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
            },
            body: JSON.stringify({
                item_creation_id: itemId,
                description: desc,
                tube_size: tubeSize,
                unit: unit,
                rate_per_unit: rate,
                quantity: qty,
            })
        })
        .then(res => res.json())
        .then(data => {
            if (data.status === 'success' && data.entry) {
                // Update row ID with real DB ID
                const row = tbody ? tbody.querySelector(`tr[data-row-id="${tempId}"]`) : null;
                if (row) {
                    row.setAttribute('data-overview-id', data.entry.id);
                    row.setAttribute('data-row-id', data.entry.id);
                    const delBtn = row.querySelector('.boc-action-del');
                    if (delBtn) delBtn.setAttribute('data-id', data.entry.id);
                }
            }
        })
        .catch(err => console.error('Error saving BOC entry:', err));
    }

    // Clear inputs
    if (descInput) descInput.value = '';
    if (sizeInput) sizeInput.value = '';
    if (unitInput) unitInput.value = '';
    if (rateInput) rateInput.value = '0.0000';
    if (qtyInput) qtyInput.value = '0';
    if (totalInput) totalInput.value = '0.00';

    recalculateSubTotals();
}

/**
 * Handle deletion of a row from Overview table when clicking ✕! button
 */
function handleDeleteRow(buttonEl) {
    const row = buttonEl.closest('tr');
    if (!row) return;

    const entryId = buttonEl.getAttribute('data-id');
    const entryType = buttonEl.getAttribute('data-type');
    const tbody = row.parentElement;

    // Remove row from DOM
    row.remove();

    // Check if table became empty
    if (tbody && tbody.children.length === 0) {
        const emptyTr = document.createElement('tr');
        emptyTr.className = 'overview-empty-row';
        emptyTr.innerHTML = `<td colspan="7" class="text-center" style="padding: 8px; color: #94A3B8; font-style: italic;">No items in overview</td>`;
        tbody.appendChild(emptyTr);
    }

    recalculateSubTotals();

    // Perform server-side deletion if entryId is numeric (persisted in DB)
    if (entryId && !entryId.toString().startsWith('new_')) {
        const formData = new FormData();
        formData.append('type', entryType || 'manual');

        fetch(`/CostingBCCal/boc/delete-entry/${entryId}/`, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
            },
            body: formData,
        })
        .then(res => res.json())
        .then(data => {
            if (data.status !== 'success') {
                console.warn('Delete failed on server:', data.message);
            }
        })
        .catch(err => console.error('Error deleting entry:', err));
    }
}

/**
 * Escape HTML utility
 */
function escapeHtml(str) {
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}
