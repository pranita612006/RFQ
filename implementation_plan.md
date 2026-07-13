# Implementation Plan - BOP Create Lifecycle Workflow

This plan outlines the changes to implement a complete, robust "Create" lifecycle workflow for BOP.

## Proposed Changes

### Backend Views & Routing

#### [MODIFY] [views.py](file:///d:/N-RFQ/apps/BOP/views.py)
1. **Refactor `get_bop_autofill_data`**:
   - Explicitly cast/extract human-readable string values for all fetched fields (specifically `cell`, `product_category`, and `customer_code` using `search_name`).
2. **Implement `save_bop_form`**:
   - Decorate with `@require_active_customer`.
   - Wrap the mutation block in `django.db.transaction.atomic`.
   - Extract and sanitize POST parameters.
   - Parse dates gracefully.
   - If a BOP record does not exist for the selected item, autogenerate a unique `bopcreation_id` (e.g. `Bop_YYYYMMDD<rand>`).
   - Create or update the `BOPCreation` record.
   - Create a corresponding `BOPCreationECN` history log with an auto-incremented `ecn_id` (e.g. `FCN-1`).
   - Return clean JSON response with statuses and identifiers.

#### [MODIFY] [urls.py](file:///d:/N-RFQ/apps/BOP/urls.py)
- Add path `"BOP/save/"` mapping to `views.save_bop_form`.

### Frontend Template

#### [MODIFY] [BOP_form.html](file:///d:/N-RFQ/apps/BOP/templates/BOP/BOP_form.html)
- Update step 1 form submission event: intercept the default form submission, serialize form data, retrieve CSRF token, send POST request to `BOP/save/`, handle response showing a toast message and updating the UI fields (like `table_id`, `bop_creation_id`, `last_ecn_no`, etc.) asynchronously.

## Verification Plan

### Manual Verification
- Select an item creation ID, ensure form fields autofill with clean string values (including cell name).
- Fill/edit drawing details, remarks, and dates.
- Click "Save" and verify:
  - Form is not reloaded.
  - SweetAlert or alert toast shows success.
  - `table_id`, `bop_creation_id`, and `last_ecn_no` are populated in the UI inputs.
  - A database query verifies `BOPCreation` and `BOPCreationECN` have correct rows inserted.
