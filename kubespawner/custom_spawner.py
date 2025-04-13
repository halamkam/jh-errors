from kubespawner import KubeSpawner
from tornado.web import HTTPError
from kubernetes_asyncio.client.exceptions import ApiException


class CustomKubeSpawner(KubeSpawner):
    async def start(self):
        try:
            return await super().start()  # Attempt to start the notebook

        except TimeoutError as e:
            # Catch a timeout error and override it to show a custom message
            self.log.error(f"Notebook spawn failed due to timeout: {e}")
            raise HTTPError(408, "Notebook failed to start: Server took too long to respond. Try again later.")

        except ApiException as e:
            # Catch Kubernetes API exceptions and handle them
            if e.status == 403:
                self.log.error(f"Notebook spawn failed due to resource quota being exceeded: {e}")
                raise HTTPError(403, "Notebook failed to start: Your resource quota has been exceeded. Contact your administrator.")
            
            elif e.status == 404:
                self.log.error(f"Notebook spawn failed due to resource not found: {e}")
                raise HTTPError(404, "Notebook failed to start: The container image was not found. Please check the selected environment or contact support.")
            
            elif e.status == 409:
                self.log.error(f"Notebook spawn failed due to conflict (possible PVC issue): {e}")
                raise HTTPError(409, "Notebook failed to start: There was a conflict with the requested resource (possible PVC issue).")
            
            else:
                self.log.error(f"Notebook spawn failed due to API error: {e}")
                raise HTTPError(500, f"Notebook failed to start: An unexpected error occurred with the Kubernetes API: {e.reason}")

        except Exception as e:
            # General catch-all error for unknown cases
            self.log.error(f"Notebook spawn failed: {e}")  # Log full error for debugging
            raise HTTPError(500, "Notebook failed to start due to an unexpected error. Please contact support.")

