import subprocess, time, json, base64, urllib.request, sys, websocket
S, url, out, wait = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
p = subprocess.Popen(["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome","--headless=new","--disable-gpu","--hide-scrollbars","--remote-debugging-port=9333","--remote-allow-origins=http://127.0.0.1:9333",f"--user-data-dir={S}/chrome-prof2","--window-size=1440,1000","about:blank"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
try:
    for _ in range(30):
        try:
            tabs = json.load(urllib.request.urlopen("http://127.0.0.1:9333/json")); break
        except Exception: time.sleep(0.5)
    ws = websocket.create_connection([t for t in tabs if t["type"]=="page"][0]["webSocketDebuggerUrl"], timeout=60)
    i = 0
    def call(m, **params):
        global i; i += 1
        ws.send(json.dumps({"id": i, "method": m, "params": params}))
        while True:
            r = json.loads(ws.recv())
            if r.get("id") == i: return r
    call("Emulation.setDeviceMetricsOverride", width=1440, height=1000, deviceScaleFactor=1, mobile=False)
    call("Page.navigate", url=url)
    time.sleep(wait)
    r = call("Page.captureScreenshot", format="png")
    open(out, "wb").write(base64.b64decode(r["result"]["data"]))
    print("saved", out)
finally:
    p.kill()
