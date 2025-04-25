import asyncio
import time
from kubespawner import KubeSpawner
from tornado.web import HTTPError
from kubernetes_asyncio.client.exceptions import ApiException


class CustomKubeSpawner(KubeSpawner):
    async def start(self):
        self._fatal_spawn_error = None

        # Run spawn and monitor concurrently
        try:
            result = await self._start_with_monitor()

            if self._fatal_spawn_error:
                self.log.error(
                    "[CustomKubeSpawner] Fatal error detected, stopping spawn."
                )
                # Ensure the pod is stopped (same way as can be seen in spawner.py/Kubespawner/_start())
                await self.stop(now=True)
                raise HTTPError(500, self._fatal_spawn_error)

            return result

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

    async def _start_with_monitor(self):
        """Runs spawn alongside event monitoring and handles race condition properly."""
        monitor_task = asyncio.create_task(self._check_pod_events_for_errors())
        spawn_coro = super().start()

        # Wait for either task to complete
        done, pending = await asyncio.wait(
            [monitor_task, spawn_coro],
            return_when=asyncio.FIRST_COMPLETED,
        )

        # Case: Fatal error detected
        if monitor_task in done and self._fatal_spawn_error:
            self.log.error(
                "[CustomKubeSpawner] Cancelling spawn due to unrecoverable error."
            )
            return None  # Skip returning a spawn URL

        # Case: Spawn finished first
        for task in done:
            if task is not monitor_task:
                return await task

        # Cancel anything left
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
        # Let the pod try to start for a few seconds before checking events
        await asyncio.sleep(5)

        self.log.info(
            f"[CustomKubeSpawner] Watching events for pod '{pod_name}' in namespace '{namespace}'..."
        )

        self.log.debug(f"[CustomKubeSpawner] Events: {self.events}")

        while time.time() - start_time < timeout:
            try:
                for event in self.events:
                    reason = event.get("reason")
                    message = event.get("message")

                    if "Failed" in reason and (
                        "ErrImagePull" in message or "ImagePullBackOff" in message
                    ):
                        self.log.error(
                            f"""[CustomKubeSpawner] Event indicates unrecoverable error: 
                            Reason: {reason}
                            Message: {message}"""
                        )
                        self._fatal_spawn_error = (
                            f"Failed to pull the notebook image.\n\nReason: {reason}\nDetails: {message}\n\n"
                            "This usually means the image doesn't exist or is misconfigured. Please contact support."
                        )
                        self.log.info("[CustomKubeSpawner] Event monitoring finished after finding an unrecoverable error.")
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

        self.log.info(f"[CustomKubeSpawner] Event monitoring finished after {timeout} seconds.")
