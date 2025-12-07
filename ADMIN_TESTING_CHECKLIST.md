# Admin Panel Testing Checklist

Test these scenarios after deploying the admin fixes.

## Test 1: Create STUDENT User ✓

**Steps:**
1. Navigate to Admin Panel > Users > Create User
2. Fill in form:
   - Email: `test.student@example.com`
   - Full Name: `Test Student`
   - **Password: `TestPassword123!`** ← NEW FIELD
   - Role: `student`
3. Click Save

**Expected Result:**
- ✓ Form submits successfully
- ✓ User is created with hashed password
- ✓ No "null value in column password_hash" error
- ✓ User appears in list
- ✓ User can login with the password

**Troubleshooting:**
If error occurs:
- Check error.log for traceback
- Verify password is not empty
- Ensure bcrypt is installed: `pip list | grep bcrypt`

---

## Test 2: Create Prompt ✓

**Steps:**
1. Navigate to Admin Panel > Prompts > Create Prompt
2. Fill in form:
   - Name: `Test Prompt`
   - Content: `You are a helpful assistant...`
   - Description: `Test description`
   - Active: `true` or `false`
3. Click Save

**Expected Result:**
- ✓ Form submits successfully
- ✓ Prompt is created
- ✓ `created_by` field is auto-set to current admin user
- ✓ No "null value in column created_by" error
- ✓ Prompt appears in list with current admin as creator

**Notes:**
- `created_by` field is NOT visible in form (auto-set)
- Check the created prompt to verify it shows current admin as creator

**Troubleshooting:**
If error occurs:
- Check error.log for traceback
- Verify admin session is active (not logged out)
- Check `request.session.get("user_id")` is not None

---

## Test 3: View Document Chunk List ✓

**Steps:**
1. Navigate to Admin Panel > Document Chunks
2. Verify list loads without error
3. Scroll through list (if multiple chunks exist)

**Expected Result:**
- ✓ List loads successfully
- ✓ Displays: ID, Document, Chunk Index, Page Number, Created
- ✓ Can search by content
- ✓ Can sort by columns
- ✓ No 500 error

**Troubleshooting:**
If error occurs:
- Run test script: `python test_document_chunk_admin.py`
- Check if document_chunk table exists
- Verify no NULL values in required fields

---

## Test 4: View Document Chunk Detail ✓ (Main Test)

**Steps:**
1. Navigate to Admin Panel > Document Chunks
2. Click on ANY row to view details
3. Verify detail view loads

**Expected Result:**
- ✓ Detail view loads WITHOUT 500 error
- ✓ Displays fields: ID, Document, Chunk Index, Content, Page Number
- ✓ Does NOT display: embedding, chunk_metadata, created_at
- ✓ Shows content text without error

**What's Hidden (and why):**
- ❌ `embedding` - Vector type (1536 dimensions), not user-friendly
- ❌ `chunk_metadata` - JSONB type, serialization issues
- ❌ `created_at` - Read-only timestamp

**Troubleshooting:**
If you still get 500 error:
1. Check browser console for error details
2. Run: `python test_document_chunk_admin.py`
3. Check error.log for full traceback:
   ```bash
   tail -100 logs/error.log
   ```
4. Look for:
   - "Vector" or "vector" errors
   - "JSONB" or serialization errors
   - "pgvector" errors
5. If issue persists, share the error traceback from logs

---

## Test 5: View Chat Session List ✓

**Steps:**
1. Navigate to Admin Panel > Chat Sessions
2. Verify list loads without error

**Expected Result:**
- ✓ List loads successfully
- ✓ Displays session info without 500 error

---

## Test 6: View Chat Session Detail ✓

**Steps:**
1. Navigate to Admin Panel > Chat Sessions
2. Click on any row to view details

**Expected Result:**
- ✓ Detail view loads WITHOUT 500 error
- ✓ Can edit: status, comprehension_level, summary
- ✓ Does NOT display: messages, interaction_messages, real_messages (JSONB fields)

---

## Test 7: Edit Existing User ✓

**Steps:**
1. Navigate to Admin Panel > Users
2. Click on an existing user
3. Modify the password field
4. Click Save

**Expected Result:**
- ✓ Password field is editable
- ✓ New password is hashed before saving
- ✓ User can login with new password
- ✓ No error when submitting

---

## Test 8: Edit Chat Session ✓

**Steps:**
1. Navigate to Admin Panel > Chat Sessions
2. Click on a session
3. Modify status or comprehension level
4. Click Save

**Expected Result:**
- ✓ Form loads without 500 error
- ✓ Editable fields: status, comprehension_level, summary, task, persona, mission_objective
- ✓ Changes are saved successfully

---

## Test 9: Delete Document Chunk ✓

**Steps:**
1. Navigate to Admin Panel > Document Chunks
2. Click on a chunk
3. Click Delete button
4. Confirm deletion

**Expected Result:**
- ✓ Chunk is deleted successfully
- ✓ No error during deletion
- ✓ Chunk disappears from list

---

## Summary Checklist

- [ ] Test 1: Create STUDENT User (with password field)
- [ ] Test 2: Create Prompt (created_by auto-set)
- [ ] Test 3: View Document Chunk List
- [ ] **Test 4: View Document Chunk Detail (no 500 error)** ← CRITICAL TEST
- [ ] Test 5: View Chat Session List
- [ ] Test 6: View Chat Session Detail (no 500 error)
- [ ] Test 7: Edit Existing User (password)
- [ ] Test 8: Edit Chat Session
- [ ] Test 9: Delete Document Chunk

---

## Common Issues & Solutions

### "Internal Server Error (500)" on Document Chunk Detail

**Cause:** SQLAdmin trying to serialize Vector/JSONB fields

**Solution Already Applied:**
- Excluded `embedding` and `chunk_metadata` from detail view
- Added type formatters for Vector type
- These fields now hidden, not displayed

**If still getting error:**
1. Clear browser cache (Ctrl+Shift+Del)
2. Hard refresh admin page (Ctrl+F5)
3. Restart backend server
4. Run test script to identify exact issue

### "null value in column password_hash"

**This should be FIXED.** Password field now required in form.

If still occurs:
- Verify `form_args` with `DataRequired()` validator exists
- Check that `User.password_hash` is in `form_excluded_columns` as False

### "null value in column created_by"

**This should be FIXED.** Prompt creation auto-sets admin user.

If still occurs:
- Verify `created_by` is in `form_excluded_columns`
- Check `on_model_change()` hook is present
- Verify `request.session.get("user_id")` returns value

---

## Additional Testing

### Test API Still Works

While admin panel is fixed, verify API endpoints still work:

```bash
# Register new user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "api.test@example.com",
    "password": "TestPassword123!",
    "full_name": "API Test User"
  }'

# Create prompt via API
curl -X POST http://localhost:8000/api/v1/prompts \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "API Prompt",
    "content": "System prompt...",
    "description": "Created via API"
  }'
```

Expected: ✓ All API endpoints work normally

---

## Success Criteria

All tests pass when:
1. ✓ User can be created with password in admin panel
2. ✓ Prompt can be created with auto-set creator
3. ✓ Document chunks can be viewed without 500 error
4. ✓ Chat sessions can be viewed without 500 error
5. ✓ All edits and deletions work
6. ✓ API endpoints still functional

---

## Report Issues

If any test fails:
1. Note the test number (e.g., "Test 4: View Document Chunk Detail")
2. Screenshot the error
3. Get the error message from error.log:
   ```bash
   tail -200 logs/error.log | grep -A 50 "ERROR"
   ```
4. Run test script:
   ```bash
   python test_document_chunk_admin.py
   ```
5. Share:
   - Test number
   - Error message
   - Error log content
   - Test script output
