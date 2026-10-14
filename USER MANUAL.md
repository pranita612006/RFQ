# 📖 FlowNexis (RFQ Tool) — User Manual

> A complete guide on how to use the FlowNexis RFQ Management Application.

---

## 📋 Table of Contents

1. [Getting Started](#-getting-started)
2. [Login & Authentication](#-login--authentication)
3. [Dashboard](#-dashboard)
4. [Customer Selection](#-customer-selection)
5. [Item Creation](#-item-creation)
6. [Opportunity Creation](#-opportunity-creation)
7. [Feasibility Form](#-feasibility-form)
8. [BOM (Bill of Materials)](#-bom-bill-of-materials)
9. [BOP (Bill of Process)](#-bop-bill-of-process)
10. [BOC (Bill of Components)](#-boc-bill-of-components)
11. [Costing & BC Calculations](#-costing--bc-calculations)
12. [Blanket Sales Order](#-blanket-sales-order)
13. [Approve Record](#-approve-record)
14. [Reports](#-reports)
15. [To-Do List](#-to-do-list)
16. [ERP Data](#-erp-data)
17. [Upload Data](#-upload-data)
18. [User Management](#-user-management)
19. [Admin Panel](#-admin-panel)
20. [Tips & Best Practices](#-tips--best-practices)

---

## 🚀 Getting Started

1. Open your web browser (Chrome, Edge, Firefox recommended)
2. Navigate to the application URL:
   - **Local:** `http://127.0.0.1:8000/`
   - **Production:** Your deployed server URL
3. You will be redirected to the **Login** page

---

## 🔐 Login & Authentication

### Logging In

1. Enter your **Username** and **Password**
2. Click the **Sign In** button
3. You will be redirected to the **Dashboard**

### Registering a New Account

1. Click the **Register** button in the sidebar (or navigate to the registration page)
2. Fill in the required fields:
   - Username
   - Email address
   - Password (enter twice to confirm)
3. Click **Register**
4. Your account will be created and you can log in immediately

### Forgot Password

1. On the login page, click **Forgot Password**
2. Enter your registered email address
3. Check your email for a password reset link
4. Click the link and set a new password

> **Note:** Password reset via email requires email configuration by the administrator.

### Logging Out

- Click the **Logout** button at the bottom of the left sidebar
- You will be redirected to the login page
- Your session is automatically cleared

---

## 📊 Dashboard

The Dashboard is the home page after login. It provides an overview of your RFQ workflow.

### Dashboard Versions

The app offers three dashboard views, accessible from the sidebar:

| Dashboard    | Description                                |
|-------------|---------------------------------------------|
| **Dashboard v1** | Default view — primary overview with key metrics |
| **Dashboard v2** | Alternative layout with different widget arrangement |
| **Dashboard v3** | Extended view with additional data panels |

### Navigation

- The **left sidebar** contains all navigation links to different modules
- The **top navigation bar** shows the current page and user info
- Use the **sidebar search** to quickly find menu items
- The sidebar displays the **currently active customer** (or a warning if none is selected)

---

## 👥 Customer Selection

> **This is typically the first step before working on any RFQ.**

### How to Select a Customer

1. Click **Customer Selection** in the sidebar
2. Browse the list of available customers or use the search functionality
3. Click on a customer to **set them as the active customer**
4. Once selected, the customer name, ID, and code will appear in the sidebar panel

### Why Customer Selection Matters

- Most modules (Item Creation, Opportunities, BOM, etc.) work in the context of the **active customer**
- The active customer is shown in the sidebar under the user panel
- If you see **"No Customer Selected"** warning, select a customer first before proceeding with other modules

---

## 📦 Item Creation

### Creating a New Item

1. Click **Item Creation** in the sidebar
2. Fill in the item details:
   - Item name / description
   - Item specifications
   - Part numbers and related details
3. Click **Save** to create the item

### ECN Request (Engineering Change Notice)

1. Navigate to the **ECN Request** page (accessible from Item Creation or via `/ecn-request/`)
2. Fill in the change request details
3. Submit the request for review

---

## 💡 Opportunity Creation

### Creating a New Opportunity

1. Click **Opportunity Creation** in the sidebar
2. Enter the opportunity details:
   - Opportunity name
   - Customer reference
   - Expected value / volume
   - Timeline and deadlines
3. Click **Save** to create the opportunity

### Managing Opportunities

- View all existing opportunities in the list
- Click on an opportunity to view/edit its details
- Track the status and progress of each opportunity

---

## 📝 Feasibility Form

### Filling Out a Feasibility Form

1. Click **Feasibility Form** in the sidebar
2. Complete all sections of the feasibility assessment:
   - Technical feasibility
   - Manufacturing capability
   - Resource requirements
   - Risk assessment
3. Click **Save** or **Submit** to record the assessment

### Purpose

The feasibility form helps evaluate whether an RFQ can be fulfilled before committing to a quotation.

---

## ⚙️ BOM (Bill of Materials)

### Creating a BOM

1. Click **BOM Creation** in the sidebar
2. Define the bill of materials for the product/item:
   - Add raw materials
   - Specify quantities
   - Set material specifications
3. Save the BOM

### Managing BOMs

- View existing BOMs in the list
- Edit or update material entries as needed
- BOMs are linked to the active customer's items

---

## 🏭 BOP (Bill of Process)

### Creating a BOP

1. Click **BOP Creation** in the sidebar
2. Define the manufacturing process steps:
   - Process sequence
   - Machine/equipment requirements
   - Cycle times
   - Labour requirements
3. Save the BOP

### Purpose

The BOP outlines the complete manufacturing process required to produce an item, used for process planning and costing.

---

## 🔗 BOC (Bill of Components)

### Creating a BOC

1. Click **BOC Creation** in the sidebar
2. Define the component breakdown:
   - Component list
   - Sub-assemblies
   - Component specifications
3. Save the BOC

### Purpose

The BOC details all components and sub-assemblies needed to build the final product.

---

## 🧮 Costing & BC Calculations

### Performing Cost Calculations

1. Click **Costing & BC Calculations** in the sidebar
2. The module pulls data from BOM, BOP, and BOC
3. Review and adjust:
   - Material costs
   - Process costs
   - Overhead and margins
   - Business case calculations
4. Generate the final costing summary

### Purpose

This module calculates the total cost of production and helps build the business case for the quotation.

---

## 📄 Blanket Sales Order

### Creating a Blanket Sales Order

1. Click **Blanket Sales Order** in the sidebar
2. Enter the sales order details:
   - Customer reference
   - Item quantities and pricing
   - Delivery schedule
   - Terms and conditions
3. Save or submit the order

### Purpose

Blanket Sales Orders are long-term purchase agreements with customers, covering multiple deliveries over a period.

---

## ✅ Approve Record

### Reviewing & Approving Records

1. Click **Approve Record** in the sidebar
2. View the list of records pending approval
3. Click on a record to review its details
4. Choose to **Approve** or **Reject** the record
5. Add comments or notes if needed

### Purpose

This module provides an approval workflow for records that require managerial or cross-functional sign-off before proceeding.

---

## 📊 Reports

### Viewing Reports

1. Click **Report** in the sidebar
2. Select the type of report you want to generate
3. Apply filters (date range, customer, status, etc.)
4. View the report data in tables or charts
5. Export reports if export options are available

### Available Report Types

Reports may include:
- RFQ status summary
- Customer-wise analysis
- Costing summaries
- Approval status tracking

---

## ✔️ To-Do List

### Managing Tasks

1. Click **To-Do List** in the sidebar
2. View your list of tasks

### Adding a Task

- Enter the task title and description
- Set a due date (optional)
- Click **Add** or **Save**

### Completing a Task

- Mark tasks as completed by clicking the checkbox or complete button
- Completed tasks are visually highlighted

---

## 🗃️ ERP Data

### Viewing ERP Data

1. Click **ERP Data** in the sidebar
2. Browse the ERP records imported into the system
3. Use search and filter options to find specific data

### Purpose

This module provides access to data synced from your ERP system, serving as a reference while working on RFQs.

---

## 📤 Upload Data

### Uploading Data Files

1. Click **Upload Data** in the sidebar
2. Click the upload button or drag-and-drop your file
3. Supported formats: **Excel (.xlsx, .xls)**, **CSV (.csv)**
4. Map the columns if prompted
5. Click **Upload** to import the data

### Purpose

Allows bulk importing of data (items, customers, materials, etc.) from spreadsheet files into the system.

---

## 👤 User Management

> **Note:** This module is typically accessible to Admin/Manager users only.

### Managing Users

1. Click **User Management** in the sidebar
2. View the list of all registered users
3. Available actions:
   - **Add** new users
   - **Edit** user details and roles
   - **Activate/Deactivate** user accounts
   - **Reset passwords** for users

### User Roles

Users may have different permission levels controlling what modules they can access.

---

## ⚡ Admin Panel

### Accessing the Admin Panel

1. Navigate to `http://127.0.0.1:8000/admin/`
2. Log in with your **superuser** credentials
3. The admin panel provides full database management:
   - View, add, edit, and delete any records
   - Manage user accounts and permissions
   - Configure system settings

> **Note:** Only superusers (created via `python manage.py createsuperuser`) can access the admin panel.

---

## 💡 Tips & Best Practices

### General Workflow

The typical RFQ workflow follows this sequence:

```
Customer Selection → Item Creation → Opportunity Creation → Feasibility Form
        ↓
   BOM Creation → BOP Creation → BOC Creation
        ↓
   Costing & BC Calculations → Approve Record → Blanket Sales Order
        ↓
      Reports
```

### Best Practices

1. **Always select a customer first** before working on items, opportunities, or any other module
2. **Save frequently** — the app does not auto-save in most modules
3. **Use the To-Do list** to track your pending RFQ tasks
4. **Check the Dashboard** regularly for an overview of your work status
5. **Upload data in bulk** via the Upload Data module to save time on repetitive entries
6. **Use the sidebar search** to quickly navigate to any module
7. **Log out when done** — sessions expire when the browser closes for security

### Keyboard Shortcuts

| Shortcut          | Action                |
|-------------------|-----------------------|
| `Ctrl + F`        | Browser search on page |
| `F5`              | Refresh the page       |
| `Alt + ←`         | Go back               |
| `Tab`             | Move to next field     |
| `Shift + Tab`     | Move to previous field |

### Browser Recommendations

| Browser          | Support     |
|-----------------|-------------|
| Google Chrome    | ✅ Recommended |
| Microsoft Edge   | ✅ Recommended |
| Mozilla Firefox  | ✅ Supported |
| Safari           | ⚠️ Basic support |
| Internet Explorer | ❌ Not supported |

---

## 🆘 Need Help?

- Contact your **system administrator** for account or access issues
- Check the **SETUP README.MD** for technical/development setup
- Report bugs or issues to the development team
