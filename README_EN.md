# 🛰️ Loon4Streaming.conf — README for Streaming-Optimized Setup

> Audience: users who want a smoother, more controllable streaming experience on **Loon** (iOS / macOS).  
> This README accompanies `Loon4Streaming.conf` and covers quick start, policy design, and troubleshooting.

---

## 🖼️ Screenshots — macOS
> macOS previews for policies & routing.

![macOS Preview 1](images/mac-1.jpg)
![macOS Preview 2](images/mac-2.jpg)
![macOS Preview 3](images/mac-3.jpg)


## 🖼️ Screenshots — iOS
> iOS previews for policies & routing.

![iOS Preview 1](images/ios-1.png)
![iOS Preview 2](images/ios-2.png)
![iOS Preview 3](images/ios-3.png)
![iOS Preview 4](images/ios-4.png)

---

## 📦 Files

> Repo structure (example)
```
/
├─ Loon4Streaming.conf
├─ README_ZH.md
├─ README_EN.md
└─ images/
   ├─ mac-1.jpg
   ├─ mac-2.jpg
   ├─ mac-3.jpg
   ├─ ios-1.png
   ├─ ios-2.png
   ├─ ios-3.png
   └─ ios-4.png
```

- **Main config**: `Loon4Streaming.conf` (tidied and ready to import)

> Tip: If you also use other managed/auto-updated profiles, avoid enabling duplicate “streaming rules/policies” to prevent conflicts or overrides.

---

## 🚀 Quick Start
1. **Install Loon**: iOS (TestFlight/App Store) or macOS (App Store/official).  
2. **Import the config**:  
   - “Profiles” → “Import from File” and choose `Loon4Streaming.conf`, or  
   - Use a remote URL (if you host this file on Git/Gist/cloud).
3. **Add nodes**: In “Nodes”, add your US / HK / SG (and other) nodes, then assign them to the respective policy groups.
4. **Check policy groups**: Open “Policies” and sort groups by your preference (e.g., priority order among US/HK/SG).
5. **Test & observe**: Run latency/speed tests in Loon; open “Logs” to verify streaming domains hit the intended policy.
6. **Start streaming**: Try Netflix / Disney+ / YouTube / Max / Spotify / Apple TV+, etc.

---

## 🧠 Routing & Policy Design
This config focuses on **recognizing popular streaming domains → mapping them to suitable regional nodes → ensuring speed & stability**.

- **Streaming master policy**: Aggregates Netflix, Disney+, YouTube, Max (HBO Max), Prime Video, Apple TV+, Spotify, etc., then dispatches to regional policies (US / HK / SG, etc.).
- **Regional policy groups**: At minimum **US / HK / SG** are included to switch or backstop availability across platforms. **Your in‑app order defines priority**, and you can adjust anytime.
- **Per‑service preferences (optional)**:  
  - **Google** prefers **HK** (YouTube / YouTube Music often fall under the streaming umbrella as well).  
  - **Apple / Microsoft** via **US** for consistent store/subscription/DRM flows.  
  - **PayPal** fixed to **US** for consistent billing/risk checks.  
  - **Rare Areas**: a bucket for niche/test nodes so they don’t pollute your main workflow.
- **Failover behavior**: If a chosen node is down or underperforms, the group will fail over to the next candidate (depends on your policy mode: priority/failover/load‑balancing).

> Real unlock scope depends on platform risk control and node quality. Keeping multiple regions ready is recommended.

---

## 🧩 Customize & Extend
- **Add a new platform**: Append its domains/keywords in the rules and point them to the Streaming policy.
- **Regional preference**: Change the order/weights inside policy groups—no need to edit rule details.
- **Allow/Deny lists**: Whitelist direct‑connect resources (e.g., local CDN/ISP‑free traffic); blacklist third‑party resolvers/accelerators that may cause misrouting.

---

## 🧪 Verification
- **Log hits**: Loon → “Logs” and confirm streaming domains hit the “Streaming” policy.  
- **Platform self‑checks**: Use Netflix playback (or `fast.com` for speed), check YouTube 4K/AV1 availability, try Apple TV+ previews.  
- **IP/Region checks**: Inspect region/billing country in account pages to ensure the expected region is applied (platform display is authoritative).

---

## 🛠️ FAQ
**Q1: Playback stutter or unstable speed?**  
A: Switch to better nodes within the same region; prefer low‑loss routes; avoid stacking with system‑level VPN/proxies.

**Q2: Netflix/Disney+ unavailable or catalog shrinks?**  
A: Switch to another region (HK/SG/US variants), clear app cache & cookies, then retry.

**Q3: Sign‑in/payment issues (e.g., PayPal verification)?**  
A: Ensure the service goes through its designated region (e.g., US). Keep billing/account region consistent; avoid frequent cross‑region logins.

**Q4: Conflicts with other managed profiles?**  
A: Don’t enable duplicate “streaming rules/policies” in multiple profiles; keep `Loon4Streaming.conf` higher priority.

**Q5: Update rules without touching my nodes/icons?**  
A: Separate rules from nodes/icons: keep rules managed, keep nodes/icons local. When updating, replace only the rules section.

---

## 🔐 Compliance & Disclaimer
- For learning and network optimization reference only. Follow your local laws/regulations and each platform’s Terms of Service.  
- Cross‑region access/subscriptions carry risks borne by the user.

---

## 🗓️ Version
- Doc updated: 2025‑10‑13 (Asia/Singapore, UTC+8)  
- Target: `Loon4Streaming.conf`

> Feedback and PRs welcome—feel free to fork and customize.
