# Task: Deploy to Production

- [ ] Planning
    - [x] Analyze deployment history and config <!-- id: 10 -->
    - [x] Identify Service Names and Regions (`session-api`, `admin-dashboard`, `us-central1`) <!-- id: 11 -->
    - [ ] **User Approval** of deployment plan <!-- id: 12 -->
- [ ] Execution
    - [ ] Merge `fix/secure-and-update-auth` into `main` <!-- id: 13 -->
    - [ ] Backend: Build & Deploy `session-api` <!-- id: 14 -->
    - [ ] Frontend: Build & Deploy `admin-dashboard` <!-- id: 15 -->
    - [ ] Functions: `firebase deploy --only functions` <!-- id: 16 -->
- [ ] Verification
    - [ ] Verify Backend Health (`/root` or `/health`) <!-- id: 17 -->
    - [ ] Verify Frontend Access <!-- id: 18 -->
