import time
from playwright.sync_api import sync_playwright

URL = "https://ryoseiimai.github.io/ai-pachinko-maker/"
VIDEO_DIR = "/Users/ryoseiworld/dev/2026-09-02-ai-pachinko-maker/evidence/video_raw"

with sync_playwright() as p:
    browser = p.chromium.launch()
    context = browser.new_context(
        viewport={"width": 1280, "height": 720},
        record_video_dir=VIDEO_DIR,
        record_video_size={"width": 1280, "height": 720},
    )
    page = context.new_page()

    # 1. トップ表示
    page.goto(URL, wait_until="networkidle")
    time.sleep(1.8)
    page.mouse.wheel(0, 300)
    time.sleep(1.8)

    # 2. エヴァンゲリオンカードをクリック
    card = page.locator("text=エヴァンゲリオン").first
    card.scroll_into_view_if_needed()
    time.sleep(0.5)
    card.click()
    time.sleep(1.0)
    # 分析パネルまでスクロール
    page.locator("#analysisPanel").scroll_into_view_if_needed()
    time.sleep(2.0)

    # 3. ランキングタブ
    page.locator('.tab-btn[data-tab="ranking"]').click()
    time.sleep(2.0)

    # 4. メーカー経営モードタブ
    page.locator('.tab-btn[data-tab="keiei"]').click()
    time.sleep(1.0)
    pick_buttons = page.locator("#keieiPickList button, #keieiPickList .card, #keieiPickList [data-id]")
    count = pick_buttons.count()
    if count == 0:
        # フォールバック: pickList内のクリック可能要素を汎用探索
        pick_buttons = page.locator("#keieiPickList *").filter(has_text="")
    clicked = 0
    # 実際の子要素を直接走査してクリック可能な最初の4件を選ぶ
    children = page.locator("#keieiPickList > *")
    n = children.count()
    for i in range(n):
        if clicked >= 4:
            break
        el = children.nth(i)
        try:
            el.click(timeout=2000)
            clicked += 1
            time.sleep(1.2)
        except Exception:
            continue
    time.sleep(1.0)
    page.locator("#keieiWarn").scroll_into_view_if_needed()
    time.sleep(2.0)

    # 5. トップへ戻る
    page.locator('.tab-btn[data-tab="candidates"]').click()
    time.sleep(1.5)

    context.close()
    browser.close()

print("done")
