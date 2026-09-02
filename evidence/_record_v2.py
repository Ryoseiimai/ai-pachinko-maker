import time
from playwright.sync_api import sync_playwright

URL = "https://ryoseiimai.github.io/ai-pachinko-maker/"
VIDEO_DIR = "/Users/ryoseiworld/dev/2026-09-02-ai-pachinko-maker/evidence/video_raw_v2"

with sync_playwright() as p:
    browser = p.chromium.launch()
    context = browser.new_context(
        viewport={"width": 1280, "height": 720},
        record_video_dir=VIDEO_DIR,
        record_video_size={"width": 1280, "height": 720},
    )
    page = context.new_page()

    # 1. トップ表示: 機種名とスコアが見える
    page.goto(URL, wait_until="networkidle")
    time.sleep(1.5)

    # 2. 別のIPで診断 x2 (結果が変わる)
    page.locator("#btnRandom").click()
    time.sleep(1.5)
    page.locator("#btnRandom").click()
    time.sleep(1.5)

    # 3. カードから鬼滅の刃を選ぶ
    page.locator("#btnPick").click()
    time.sleep(1.5)
    kimetsu = page.locator("#cardGrid .card", has_text="鬼滅の刃").first
    kimetsu.scroll_into_view_if_needed()
    time.sleep(0.5)
    kimetsu.click()
    time.sleep(1.5)

    # 4. 分析パネル(リスク文が見える位置まで)
    page.locator("#analysisBody").scroll_into_view_if_needed()
    page.mouse.wheel(0, 200)
    time.sleep(1.5)

    # 5. ランキングタブ
    page.locator('.tab-btn[data-tab="ranking"]').click()
    time.sleep(1.5)

    # 6. 経営モードで4件編成
    page.locator('.tab-btn[data-tab="keiei"]').click()
    time.sleep(1.5)
    children = page.locator("#keieiPickList > *")
    n = children.count()
    clicked = 0
    for i in range(n):
        if clicked >= 4:
            break
        el = children.nth(i)
        try:
            el.click(timeout=1500)
            clicked += 1
            time.sleep(1.5)
        except Exception:
            continue

    # 7. 警告が出る
    page.locator("#keieiWarn").scroll_into_view_if_needed()
    time.sleep(1.5)

    context.close()
    browser.close()

print("done, clicked =", clicked)
