# Robust Git Workflow and Update Process

## **Best Practices**

1. **Commit Regularly with Clear Messages**:
   - Commit often, using descriptive messages:
     ```
     git add .
     git commit -m "Fixed bug in CSV parsing for edge cases"
     ```

2. **Use Feature Branches**:
   - Work on a new branch for every feature or update:
     ```
     git checkout -b feature-new-functionality
     ```
   - Merge into `main` only after thorough testing:
     ```
     git checkout main
     git merge feature-new-functionality
     git push origin main
     ```

3. **Test Before Pushing**:
   - Always test locally before pushing:
     ```
     python app.py
     ```

4. **Rollback if Needed**:
   - Identify stable commits with:
     ```
     git log
     ```
   - Revert changes:
     ```
     git revert <commit-hash>
     ```

5. **Tag Stable Releases**:
   - Create tags for stable points in your code:
     ```
     git tag -a v1.0 -m "Stable release"
     git push origin v1.0
     ```

---

## **Steps to Update**

1. **Pull Latest Code**:
    ```
   git pull origin main
    ```

2. **Create Feature Branch**:
    ```
   git checkout -b feature-update
    ```

3. **Run `download_data.py`**:
- Ensure your CSVs are up-to-date:
  ```
  python download_data.py
  ```

4. **Add and Commit Changes**:
    ```
   git add . git commit -m "Updated CSV data for new season"
    ```

5. **Push to GitHub**:
    ```
    git push origin feature-update
   ```
   

6. **Test Locally**:
- Run the app and verify:
  ```
  python app.py
  ```

7. **Merge and Deploy**:
- Once tested, merge to `main` and deploy:
  ```
  git checkout main
  git merge feature-update
  git push origin main
  ```

---

## **Rollback Procedure**

- If something breaks after pushing:
1. Check history:
  ```
  git log
  ```
2. Rollback to a previous stable commit:
  ```
  git checkout <stable-commit-hash>
  ```

---