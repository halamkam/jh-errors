import asyncio
import time
from kubespawner import KubeSpawner
from tornado.web import HTTPError
from kubernetes_asyncio.client.exceptions import ApiException


class CustomKubeSpawner(KubeSpawner):
    async def start(self):
        self._fatal_spawn_error = None

        # Create tasks
        spawn_task = asyncio.create_task(super().start())
        monitor_task = asyncio.create_task(self._check_pod_events_for_errors())

        done, pending = await asyncio.wait(
            [spawn_task, monitor_task],
            return_when=asyncio.FIRST_COMPLETED,
        )

        try:
            if monitor_task in done and self._fatal_spawn_error:
                self.log.error(
                    "[CustomKubeSpawner] Fatal error detected, aborting spawn."
                )
                await self.stop(now=True)
                raise HTTPError(500, self._fatal_spawn_error)

            if spawn_task in done:
                return await spawn_task

        except ApiException as e:
            if e.status == 403:
                self.log.error(
                    f"[CustomKubeSpawner] Notebook spawn failed due to resource quota being exceeded: {e}"
                )
                raise HTTPError(
                    403,
                    "Notebook failed to start: Your resource quota has been exceeded. Contact your administrator.",
                )
            else:
                self.log.error(
                    f"[CustomKubeSpawner] Notebook spawn failed due to API error: {e}"
                )
                raise HTTPError(
                    500,
                    f"Notebook failed to start: An unexpected error occurred with the Kubernetes API: {e.reason}. Please contact support.",
                )

        except Exception as e:
            self.log.error(f"[CustomKubeSpawner] Notebook spawn failed: {e}")
            raise HTTPError(
                500,
                str(e)
                if isinstance(e, HTTPError)
                else "Notebook failed to start due to an unexpected error. Please contact support.",
            )

        finally:
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

    async def _check_pod_events_for_errors(self, timeout=30):
        """Monitors Kubernetes events for the pod and detects unrecoverable errors."""
        namespace = self.namespace
        pod_name = self.pod_name
        start_time = time.time()

        self.log.info(
            f"[CustomKubeSpawner] Watching events for pod '{pod_name}' in namespace '{namespace}'..."
        )

        while time.time() - start_time < timeout:
            try:
                for event in self.events:
                    reason = event.get("reason")
                    message = event.get("message")
                    self.log.debug(
                        f"[CustomKubeSpawner] Event reason: {reason} - Event message: {message}"
                    )

                    if "Failed" in reason and (
                        "ErrImagePull" in message or "ImagePullBackOff" in message
                    ):
                        self.log.error(
                            f"[CustomKubeSpawner] Event indicates unrecoverable error: {reason} - {message}"
                        )
                        self._fatal_spawn_error = (
                            f"Failed to pull the notebook image.\n\nReason: {reason}\nDetails: {message}\n\n"
                            "This usually means the image doesn't exist or is misconfigured. Please contact support."
                        )
                        return

                await asyncio.sleep(2)

            except asyncio.CancelledError:
                self.log.info("[CustomKubeSpawner] Event monitoring cancelled.")
                break

            except Exception as e:
                self.log.warning(
                    f"[CustomKubeSpawner] Unexpected error while checking events: {e}"
                )
                break
