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

### **TODO**

1. Properly test all the implemented errors and their handling and document the tests in the `Tests` section of the notes. Also, document any encountered bugs in the `Known Bugs` section and describe how the bug was fixed.
2. Maybe try to handle the `Quota Exceeded` error in a similar fashion to those that we handle through event monitoring (the message doesn't display the event reason and message - or rather in this case the exception reason and message), which to make in uniform with the other 3 errors it should. Also I'm not sure if the 403 ApiException can't be raised in a different case, which would make this handling faulty is this assumes that `ApiException` with code 403 is only thrown when the quota is exceeded.

### **Questions**

- What should I do next? In the Word document, there is multiple things mentioned that need to be done after implementing the error handling of quota exceeded with resources, unavailable resources (within quota), non-existent image and non-existent regular PVC. These have been handled (along with the spawn cancelling). So what now?
  - Do I add code from production hub to test it with the full form used in production?
  - Do I test all this still in my own namespace and enviornment, or do I do this in some kind of test/dev enviornment of the actual hub?
  - There was a mention of some kind of storage-related errors as well (I assume these are the "special" PVCs `sshfs` and `s3`). Do I work on these (and what actually are these)?
  - Do I implement the AI callbacks in order to replace these error messages that I have currently in place?

### **Notes**

- "ked sa dany notebook ma zmazat (napr. pri neopravitelnej chybe), pomazu sa s nim i jeho eventy. Vytvorenie ntb je sprevadzane kopu eventami a ked v rychlom slede za sebou vytvoris novy ntb s tym istym nazvom, tak ti v tej pending page vypisuje este eventy stareho ntb (kubectl get events –n [namespace] ti ukaze tie eventy)" 
  - There is not much that can be done with the `kubectl get events -n [namespace]`, not from JupyterHub or KubeSpawner anyway - however on the `pending` page, these old events shouldn't be displayed anymore (they are being deleted during the `start()` method call, however I don't know how this is displayed on the production hub right now).

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
User specifies a container image that does not exist or cannot be pulled.

**Previous Behavior:**
- Once invoked, the spawn stays in the `pending` state indefinitely (until the spawn times out based on the value of `start_timeout` in the `jupyerhub_config.py` / fetched from `values.yaml`) .

- On the `spawn-pending` page that is displayed for the user while waiting for the notebook to start, the user can see warnings in the `Event log` on the page suggesting that something is wrong with the spawn, however the spawn does not get stopped nor can the user stop it or adjust the image. **Note that the spawn can't be stopped by pressing the `Stop my server` button.**. 
  - On the ***Dev hub***, pressing the button gives the following pop-up: `API request failed (400): user1 is pending check, please wait.`
  - On the ***Infra production hub***, pressing the button does not inform user of anything (no pop-up is displayed).

- After the notebook spawn times out, the spawn fails with a `TimeoutError` that gets displayed to the user.

**New Behavior:**
- Once invoked, the spawn fails (after a few seconds by raising an `HTTPError`) and displays a human-readable short and concise message stating the reason for the failure and prompting the user to contact the administrator if the issue persists.

- The spawn's failure is decided by a newly implemented event monitoring routine (custom spawner's method `_check_pod_events_for_errors(timeout=30)`), which looks for specific **event reasons and messages**, by which the routine identifies an unrecoverable error and stops the spawn instead of waiting around in the `pending` state until the spawn times out.

- The `_check_pod_events_for_errors(timeout=30)` method is started alongside the `start()` method and has a default 30 second timeout (we assume the spawn will either be successful or and unrecoverable error will be found by that point). The monitoring routine has a 5 second delay, however, to give `start()` method enough time to filter old events and to try to actually start the notebook.

- When the spawn is stopped, all the tasks/events related to the spawn are cancelled and cleaned up by calling the spawner's `stop()` method and cancelling the pending `start()` method.

- Reloading results in a `HTTP 500: Internal server error` (since reloading means the URL remains unchanged looking like this: `https://jh-error.dyn.cloud.e-infra.cz/hub/spawn-pending/user1?_xsrf=2%7C3ff4198b%7Cdacde6d671cfcd3c11e427383c6ee687%7C1745340318`). This is retrying to acccess the pending spawn that has already been cancelled when the `HTTPError` was raised.

- Going back to the `Home page` and pressing the `Start My Server` button takes the user back to the spawn form and allows them to try again.
---

### 3. Unavailable Resources (409 - Conflict)

**Cause:**  
User requests resources that are technically allowed by quota but not available on any node in the cluster (e.g. 120 CPUs).

**Previous Behavior:**
- Once invoked, the spawn stays in the `pending` state indefinitely (until the spawn times out based on the value of `start_timeout` in the `jupyerhub_config.py` / fetched from `values.yaml`) .

- On the `spawn-pending` page that is displayed for the user while waiting for the notebook to start, the user can see warnings in the `Event log` on the page suggesting that something is wrong with the spawn, however the spawn does not get stopped nor can the user stop it or adjust the image. **Note that the spawn can't be stopped by pressing the `Stop my server` button.**. 
  - On the ***Dev hub***, pressing the button gives the following pop-up: `API request failed (400): user1 is pending check, please wait.`
  - On the ***Infra production hub***, pressing the button does not inform user of anything (no pop-up is displayed).

- After the notebook spawn times out, the spawn fails with a `TimeoutError` that gets displayed to the user.

**New Behavior:**
- Once invoked, the spawn fails (after a few seconds by raising an `HTTPError`) and displays a human-readable short and concise message stating the reason for the failure and prompting the user to contact the administrator if the issue persists.

- The spawn's failure is decided by a newly implemented event monitoring routine (custom spawner's method `_check_pod_events_for_errors(timeout=30)`), which looks for specific **event reasons and messages**, by which the routine identifies an unrecoverable error and stops the spawn instead of waiting around in the `pending` state until the spawn times out.

- The `_check_pod_events_for_errors(timeout=30)` method is started alongside the `start()` method and has a default 30 second timeout (we assume the spawn will either be successful or and unrecoverable error will be found by that point). The monitoring routine has a 5 second delay, however, to give `start()` method enough time to filter old events and to try to actually start the notebook.

- When the spawn is stopped, all the tasks/events related to the spawn are cancelled and cleaned up by calling the spawner's `stop()` method and cancelling the pending `start()` method.

- Reloading results in a `HTTP 500: Internal server error` (since reloading means the URL remains unchanged looking like this: `https://jh-error.dyn.cloud.e-infra.cz/hub/spawn-pending/user1?_xsrf=2%7C3ff4198b%7Cdacde6d671cfcd3c11e427383c6ee687%7C1745340318`). This is retrying to acccess the pending spawn that has already been cancelled when the `HTTPError` was raised.

- Going back to the `Home page` and pressing the `Start My Server` button takes the user back to the spawn form and allows them to try again.
---

### 4. Non-existent regular PVC (404 - Not Found)

**Cause:**
User specifies a `PersistentVolumeClaim (PVC)` in the spawn form that does not exist in the current namespace.

**Previous Behavior:**
- Once invoked, the spawn stays in the `pending` state indefinitely (until the spawn times out based on the value of `start_timeout` in the `jupyerhub_config.py` / fetched from `values.yaml`) .

- On the `spawn-pending` page that is displayed for the user while waiting for the notebook to start, the user can see warnings in the `Event log` on the page suggesting that something is wrong with the spawn, however the spawn does not get stopped nor can the user stop it or adjust the image. **Note that the spawn can't be stopped by pressing the `Stop my server` button.**. 
  - On the ***Dev hub***, pressing the button gives the following pop-up: `API request failed (400): user1 is pending check, please wait.`
  - On the ***Infra production hub***, pressing the button does not inform user of anything (no pop-up is displayed).

- After the notebook spawn times out, the spawn fails with a `TimeoutError` that gets displayed to the user.

**New Behavior:**
- Once invoked, the spawn fails (after a few seconds by raising an `HTTPError`) and displays a human-readable short and concise message stating the reason for the failure and prompting the user to contact the administrator if the issue persists.

- The spawn's failure is decided by a newly implemented event monitoring routine (custom spawner's method `_check_pod_events_for_errors(timeout=30)`), which looks for specific **event reasons and messages**, by which the routine identifies an unrecoverable error and stops the spawn instead of waiting around in the `pending` state until the spawn times out.

- The `_check_pod_events_for_errors(timeout=30)` method is started alongside the `start()` method and has a default 30 second timeout (we assume the spawn will either be successful or and unrecoverable error will be found by that point). The monitoring routine has a 5 second delay, however, to give `start()` method enough time to filter old events and to try to actually start the notebook.

- When the spawn is stopped, all the tasks/events related to the spawn are cancelled and cleaned up by calling the spawner's `stop()` method and cancelling the pending `start()` method.

- Reloading results in a `HTTP 500: Internal server error` (since reloading means the URL remains unchanged looking like this: `https://jh-error.dyn.cloud.e-infra.cz/hub/spawn-pending/user1?_xsrf=2%7C3ff4198b%7Cdacde6d671cfcd3c11e427383c6ee687%7C1745340318`). This is retrying to acccess the pending spawn that has already been cancelled when the `HTTPError` was raised.

- Going back to the `Home page` and pressing the `Start My Server` button takes the user back to the spawn form and allows them to try again.
---

## 5. Tests

### 🔍 Quota Exceeded (403 - Forbidden)

**Test Setup:**\
Use the spawn form to request CPU or memory above the user’s quota (e.g., 64 GB memory if your quota is only 40 GB).  
Use a valid image and avoid invalid PVCs.

**Expected Behavior:**\
Spawn is blocked by Kubernetes quota enforcement.  
Spawner raises an `ApiException` with status 403.  
Error is caught and a user-friendly message is shown:
```
Notebook failed to start: Your resource quota has been exceeded. Contact your administrator.

If this issue persists, please contact your administrator at k8s@ics.muni.cz.
```

**Observed Behavior:**\
The spawn is cancelled right away and the correct error message with the correct exception is being raised.

**Status:**\
✅

**Notes:**\
This is currently the only error caught outside the event monitoring system.  
A future refactor might migrate this to the unified monitoring approach for consistency.

---

### 🔍 Image Not Found (404 - Not Found)

**Test Setup:**\
Use the spawn form and set the image field to:
```
nonexistent.registry.io/broken-image:latest
```
Set CPU/memory to reasonable values to avoid other errors.  
Submit the form to trigger the spawn.

**Expected Behavior:**\
Spawn begins and fails within ~10 seconds.  
Event `ErrImagePull` or `ImagePullBackOff` is logged.  
Event monitoring cancels the spawn.  
User sees a message like:
```
Failed to pull the notebook image.

Reason: <event.reason>
Details: <event.message>

If this issue persists, please contact your administrator at k8s@ics.muni.cz.
```

**Observed Behavior:**\
The spawn is cancelled after 5-10 seconds and the correct error message with the correct exception is being raised.

**Status:**\
✅

**Notes:**\
Confirm that retrying with a valid image proceeds normally.  
Confirm no lingering error state from a previous failed spawn.

---

### 🔍 Unavailable Resources (409 - Conflict)

**Test Setup:**\
Use the spawn form and request a very high number of CPUs (e.g., 120).  
Use a valid image and skip PVC to avoid unrelated issues.  
Submit the form to trigger the spawn.

**Expected Behavior:**\
Spawn begins and fails quickly (~5–15 seconds).  
`FailedScheduling` event logs: `Insufficient cpu` or `Insufficient memory`.  
Event monitoring detects and cancels the spawn.  
User sees a message like:
```
Failed to schedule the notebook server due to insufficient resources.

Reason: <event.reason>
Details: <event.message>

If this issue persists, please contact your administrator at k8s@ics.muni.cz.
```

**Observed Behavior:**\
The spawn is cancelled after 5-10 seconds and the correct error message with the correct exception is being raised.

**Status:**\
✅

**Notes:**\
Test both CPU and memory over-requests.  
Confirm retrying with valid values succeeds.

---

### 🔍 Non-existent PVC (404 - Not Found)

**Test Setup:**\
Use the spawn form and enter a PVC name that does not exist in the current namespace (e.g., `lol`).  
Set image and resource values to something valid.

**Expected Behavior:**\
Spawn begins and fails quickly (~5–10 seconds).  
A `FailedScheduling` event is logged with message: `persistentvolumeclaim "lol" not found`.  
Event monitoring detects and cancels the spawn.  
User sees a message like:
```
Notebook failed to start because the specified PersistentVolumeClaim (PVC) was not found.

Reason: <event.reason>
Details: <event.message>

If this issue persists, please contact your administrator at k8s@ics.muni.cz.
```

**Observed Behavior:**\
The spawn is cancelled after 5-10 seconds and the correct error message with the correct exception is being raised.

**Status:**\
✅

**Notes:**\
Ensure that retrying with a valid PVC (e.g., `jh-errors-pvc`) spawns the notebook successfully.

## 6. Known Bugs

### 🐞 `Image Not Found` error affects later spawns

**Problem:**  
Invoking the `Image Not Found` error spawn and then invoking any other type of spawn — whether successful or another error (such as `Quota Exceeded` or `Unavailable Resources`) — resulted in the spawn being stopped and the `Image Not Found` error incorrectly displayed on the `spawn-pending` page.

**Cause:**  
The event monitoring routine was checking `self.events` too early. It found leftover events (`ErrImagePull`) from a previous pod with the same name before the current spawn's events were filtered.

**Fix:**  
Introduced a **5-second delay** before starting the event monitoring routine. This allows the spawner’s `start()` method to set `self._last_event`, ensuring only **new** events are considered. Old events no longer affect the new spawn.

---
