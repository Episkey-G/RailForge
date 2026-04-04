class NoopPlaywrightAdapter:
    def summarize(self, workspace):
        return {"status": "skipped", "summary": "playwright adapter not configured"}

