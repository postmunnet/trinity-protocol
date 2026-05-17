# 📏 Universal Coding Standards

> **Objective**: Code that is readable, maintainable, and secure.

## 1. Core Principles (The "Universal Truths")
- **DRY (Don't Repeat Yourself)**: If you copy-paste code, abstract it into a helper or method.
- **KISS (Keep It Simple, Stupid)**: Prefer clear code over clever code.
- **YAGNI (You Ain't Gonna Need It)**: Do not build features "for the future". Solve the current problem.

## 2. Security Standards (Non-Negotiable)
- **Input Validation**: Never trust `$_GET`, `$_POST`, or user input. Always sanitize.
- **SQL Injection**: ALWAYS use Query Builder or Prepared Statements.
  - ❌ `query("SELECT * FROM users WHERE id = $id")`
  - ✅ `$this->db->where('id', $id)->get('users')`
- **XSS Prevention**: Escape output in views.
  - ✅ `echo htmlspecialchars($var);`

## 3. Performance Standards
- **No N+1 Queries**: Do not run SQL queries inside a loop. Fetch data first, then map it.
- **Index Usage**: Ensure `WHERE` clauses use indexed columns.

## 4. Documentation Standards
- **Self-Documenting Code**: Variable names should explain what they hold (`$userList` vs `$u`).
- **DocBlocks**: Complex functions must have standard DocBlocks explaining parameters and return types.

## 5. Technology Specifics ({{FRAMEWORK}})
*Note: While this file is universal, these are the active stack rules.*
- **Controllers**: Keep them thin. Logic belongs in Models or Libraries.
- **Models**: Handle all database interactions here.
- **Views**: No logic allowed. Only display variables.
- **Legacy Compatibility**: Do not break PHP 5.6/7 compatibility unless specified.
