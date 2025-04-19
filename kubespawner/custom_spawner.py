from kubespawner import KubeSpawner
from tornado.web import HTTPError
from kubernetes_asyncio.client.exceptions import ApiException


class CustomKubeSpawner(KubeSpawner):
    async def start(self):
        try:
            return await super().start()

        except ApiException as e:
            if e.status == 403:
                self.log.error(
                    f"Notebook spawn failed due to resource quota being exceeded: {e}"
                )
                raise HTTPError(
                    403,
                    "Notebook failed to start: Your resource quota has been exceeded. Contact your administrator.",
                )
            else:
                self.log.error(f"Notebook spawn failed due to API error: {e}")
                raise HTTPError(
                    500,
                    f"Notebook failed to start: An unexpected error occurred with the Kubernetes API: {e.reason}. Please contact support.",
                )

        except Exception as e:
            self.log.error(f"Notebook spawn failed: {e}")
            raise HTTPError(
                500,
                str(e)
                if isinstance(e, HTTPError)
                else "Notebook failed to start due to an unexpected error. Please contact support.",
            )
