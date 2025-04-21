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

### 4. Non-existent PVC (Error Code TBD)

Cause:

- To be specified.
