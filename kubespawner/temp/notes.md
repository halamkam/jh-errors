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

1. Refine the error messages that are displayed for the end user (add the administrator contact mail for example...)
2. Properly test all the implemented errors and their handling and document the tests in the `Tests` section of the notes. Also, document any encountered bugs in the `Known Bugs` section and how the bug was fixed.
3. Based on the Word document, add more steps to this section of **What's next?** (Storage-related errors?, AI calls?, ...)
 

Try to set `start_timeout` in `jupyterhub_config.py` to let's say 60 seconds to see if it kills the spawn after that time (for `Unavailable Resources` error). - this works as expected

Both `Unavailable Resoruces` and `Non-existent regular PVC` errors are being handled in the same way as the `Image Not Found` error - so far so good, just need to test it as stated in the step 4 of this section. To test the correct mount of PVC, just fill `jh-errors-pvc` this in the spawn form.




## 4. Errors

### 1. Quota Exceeded (403 - Forbidden)

**Cause:**  
User requests more resources than allowed by the quota set for them via `requests.cpu` and `requests.memory` (Kubernetes resource management).

**Current Behavior:**
- Custom message is shown via catching `ApiException` in the custom spawner.
- After failure, everything is cleaned up (automatically by the JupyterHub).
- User needs to return to the home page before trying to spawn their notebook again. (Simply pressing F5/Ctrl+R does not suffice as that will try to reload the specific spawning page and gives back 500 Internal server error).

**Note:** On the infra production hub, this error doesn’t occur easily, likely due to overly generous quotas - I wasn't able to reproduce this error myself, however it can probably still occur for other users with lower resource allowance.

**Future Solution:**
- Catch the error.
- Display a user-friendly error message.
- (Not yet implemented) Display current `requests.cpu` and `requests.memory` values, or implement an AI helper that recommends valid values.
- (Optional) Add redirect back to the home page for the user to not try and refresh but click the button to go to home page and try again from there. (URL for this should be found as the value of variable `spawner.hub.base_url`).
- Allow the user to try again.


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

**Hint:**  
Check the pod logs for the singleuser notebook. Look for warning messages and pod state.

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
