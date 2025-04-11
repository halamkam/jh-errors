from kubespawner import KubeSpawner
from tornado.web import HTTPError
from kubernetes_asyncio.client.exceptions import ApiException
import time

class CustomKubeSpawner(KubeSpawner):
    async def start(self):
        try:
            # TODO: Add artificial delay for timeout testing, remove after
            # time.sleep(10)
            return await super().start()  # Attempt to start the notebook

        except TimeoutError as e:
            # Catch a timeout error and override it to show a custom message
            self.log.error(f"Notebook spawn failed due to timeout: {e}")
            raise HTTPError(408, "Notebook failed to start: Server took too long to respond. Try again later.")

        except ApiException as e:
            # Catch a 
            self.log.error(f"Notebook spawn failed due to resource quota being exceeded: {e}")
            raise HTTPError(403, "Notebook failed to start: Your resource quota has been exceeded. Contact your administrator.")

        except Exception as e:
             # General catch-all error for unknown cases
            self.log.error(f"Notebook spawn failed: {e}")  # Log full error for debugging
            raise HTTPError(500, "Notebook failed to start due to an unexpected error. Please contact support.")
