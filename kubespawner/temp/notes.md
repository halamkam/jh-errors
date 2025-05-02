# JupyterHub error handling enhancement

## 1. Running the Application

### In `/srv/jupyterhub`

```
jupyterhub --config /usr/local/lib/python3.11/site-packages/kubespawner/temp/jupyterhub_config.py --debug --upgrade-db
```

## 2. Codebase Location

Both **JupyterHub** and **Kubespawner** live in:

```
/usr/local/lib/python3.11/site-packages/
```

While the **html templates** are located in:

```
/usr/local/share/jupyterhub/
```

## 3. Notes

### **What's next?**

1. Properly document all errors that are being handled so far - strucutre like the `Quota Exceeded` error. 
2. Properly test all the implemented errors and their handling and document the tests in the `Tests` section of the notes. Also, document any encountered bugs in the `Known Bugs` section and how the bug was fixed.
3. Maybe try to handle the `Quota Exceeded` error in a similar fashion to those that we handle through event monitoring (the message doesn't display the event reason and message - or rather in this case the exception reason and message), which to make in uniform with the other 3 errors it should. Also I'm not sure if the 403 ApiException can't be raised in a different case, which would make this handling faulty is this assumes that `ApiException` with code 403 is only thrown when the quota is exceeded.
4. Based on the Word document, add more steps to this section of **What's next?** (Storage-related errors?, AI calls?, ...)

## 4. Errors

### 1. Quota Exceeded (403 - Forbidden)

**Cause:**  
User requests more resources than allowed by the quota set for them via `requests.cpu` and `requests.memory` (Kubernetes resource management).

**Previous Behavior:**
- Once invoked, the spawn fails and displays the whole `ApiException` object as a string (with HTTP response headers and response body).

- When the spawn is stopped (when the `ApiException` gets raised), all the tasks/events related to the spawn are cancelled and cleaned up by the `JupyterHub` automatically.

- Reloading results in a `HTTP 500: Internal server error` (since reloading means the URL remains unchanged looking like this: `https://jh-error.dyn.cloud.e-infra.cz/hub/spawn-pending/user1?_xsrf=2%7C3ff4198b%7Cdacde6d671cfcd3c11e427383c6ee687%7C1745340318`). This is retrying to acccess the pending spawn that has already been cancelled when the `ApiException` was raised.

- Going back to the `Home page` and pressing the `Start My Server` button takes the user back to the spawn form and allows them to try again.

**New Behavior:**
- Once invoked, the spawn fails and displays a human-readable short and concise message stating the reason for the failure and prompting the user to contact the administrator if the issue persists.

- When the spawn is stopped (when the `ApiException` gets raised), all the tasks/events related to the spawn are cancelled and cleaned up by the `JupyterHub` automatically.

- Reloading results in a `HTTP 500: Internal server error` (since reloading means the URL remains unchanged looking like this: `https://jh-error.dyn.cloud.e-infra.cz/hub/spawn-pending/user1?_xsrf=2%7C3ff4198b%7Cdacde6d671cfcd3c11e427383c6ee687%7C1745340318`). This is retrying to acccess the pending spawn that has already been cancelled when the `ApiException` was raised.

- Going back to the `Home page` and pressing the `Start My Server` button takes the user back to the spawn form and allows them to try again.

**Future Enhancements:**

- (***TBD***) Display current `requests.cpu` and `requests.memory` values, or implement an AI helper that recommends valid values. For now, the message is basically a human-readable placeholder, but the AI call should suggest some steps the user can take to avoid getting the error (before trying to contact the administrators).

- (***Optional***) Add redirect back to the home page for the user to not try and refresh but click the button to go to home page and try again from there. (URL for this should be found as the value of variable `spawner.hub.base_url`. This would however mean the frontend templates need to be adjusted).

---

### 2. Image Not Found (404 - Not Found)

**Cause:**  
User enters a non-existent image name.

**Testing:**
To invoke this error, put `nonexistent.registry.io/broken-image:latest` in the image form when spawning a notebook.

**Current Behavior:**
- Spawn begins and tries to pull the image.
- Logs: `ErrImagePull` warning appears.
- Notebook remains in pending state.
- Stop button results in:
  - **Dev Hub:** Error popup: `API request failed (400): user1 is pending check, please wait.`
  - **Infra Prod Hub:** Stop button does nothing.

**Future Solution:**
- Detect and catch this error early.
- Kill the notebook spawn process (clean up all associated events).
- Show a user-friendly error message.
- Allow the user to try again.

---

### 3. Unavailable Resources (Error Code TBD)

**Cause:**  
- Request is within quota, but not enough actual resources are available in the cluster (e.g., requesting 120 CPUs when only one node is available with fewer resources).
- Notebook stays in spawning phase indefinitely.

**Solution:**
- Treat similarly to the "Image Not Found" case.
- Catch the error.
- Kill the spawn and clean up.
- Display an informative, friendly error message.
- Allow retry.
- (Future Enhancement) Use an AI helper to analyze available resources and suggest a valid configuration.

### 4. Non-existent regular PVC (Error Code TBD)

Cause:

- To be specified.

## 5. Tests

## 6. Known Bugs

### 🐞 `Image Not Found` error affects later spawns

**Problem:**  
Invoking the `Image Not Found` error spawn and then invoking any other type of spawn — whether successful or another error (such as `Quota Exceeded` or `Unavailable Resources`) — resulted in the spawn being stopped and the `Image Not Found` error incorrectly displayed on the `spawn-pending` page.

**Cause:**  
The event monitoring routine was checking `self.events` too early. It found leftover events (`ErrImagePull`) from a previous pod with the same name before the current spawn's events were filtered.

**Fix:**  
Introduced a **5-second delay** before starting the event monitoring routine. This allows the spawner’s `start()` method to set `self._last_event`, ensuring only **new** events are considered. Old events no longer affect the new spawn.

---
