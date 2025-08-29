# 📑 Smart CLI — Terminal Çıxışı Dizayn Sənədi

## 1. Orchestrator-un rolu
Terminal çıxışında **Orchestrator** mütləq görünməlidir:
- **Başlanğıc** – planı qurur və istifadəçiyə göstərir.
- **Hər fazada** – agentləri işə salır (“dispatching” mesajı).
- **Arada** – nəticələri toplayır, status bildirir.
- **Yekunda** – bütün run-ı xülasə edir.

---

## 2. Çıxışın ümumi strukturu
Hər run aşağıdakı bloklardan ibarət olmalıdır:
1. **Başlıq & Banner**  
2. **Orchestrator Initialization**  
3. **Phases (Analysis → Architecture → Implementation → Testing → Debug → Review → Meta)**  
   - Orchestrator dispatch mesajı  
   - Agentlər işə başlayır  
   - Agentlərin nəticələri və hadisələr  
4. **Final Summary (Orchestrator tərəfindən)**  

---

## 3. Başlıq və Orchestrator start
```
>S_  Smart CLI
------------------------------------
  Intelligent Code Assistant
------------------------------------

🤖 Orchestrator: Initializing Smart CLI...
   - Collecting context
   - Classifying request
   - Creating phase plan (Analysis → Architecture → Implementation → Testing → Review → Meta)
```

---

## 4. Analysis Phase
```
🤖 Orchestrator: Dispatching [Analysis Phase]

🔍 Analyzer Agent: Starting static & semantic scan...
   Progress: [■■■■■□□□] 62%
   Findings: 3 warnings, 0 critical

Events:
  00:03 🧠 Cache hit: lint-fast(7 files)
  00:04 ⚠️ Possible N+1 query in user_repo.getAll()

✅ Analyzer Agent completed → artifacts/analysis/analysis_report.json

🤖 Orchestrator: Analysis phase completed (8.2s)
```

---

## 5. Architecture Phase
```
🤖 Orchestrator: Dispatching [Architecture Phase]

🏗️ System Architect Agent: Generating system design...
   Progress: [■■■■■■□□] 78%
   Work packages created: 3

Artifacts:
  - artifacts/architecture/architecture.json
  - artifacts/architecture/work_packages.json

✅ System Architect Agent completed

🤖 Orchestrator: Architecture phase completed (4.1s)
```

---

## 6. Implementation Phase
```
🤖 Orchestrator: Dispatching [Implementation Phase]

🔧 Code Modifier Agent: Applying patch (wp-1)
   Diff preview:
   --- a/src/repo/user.py
   +++ b/src/repo/user.py
   @@
   - return db.users.all()
   + return db.users.select(...).prefetch_related("roles")

✅ Patch wp-1 applied
⏳ Waiting lock for wp-2 (src/repo/user.py)

✅ Code Modifier Agent completed (3 patches applied)
Artifacts: artifacts/implementation/change_set.json

🤖 Orchestrator: Implementation phase completed (7.3s)
```

---

## 7. Testing Phase
```
🤖 Orchestrator: Dispatching [Testing Phase]

🧪 Testing Agent: Running unit tests (4 shards)
   Progress: [■■■■■■■□] 80% → pass:123 fail:1

❌ Test failed: test_auth_token_expired
🤖 Orchestrator: Failure detected → activating Debug Agent

🧪 Integration tests: pending
🧪 Perf tests: p95=142ms (baseline 210ms) ✅
Artifacts: artifacts/testing/test_report.json
```

---

## 8. Debug Phase (şərti)
```
🤖 Orchestrator: Dispatching [Debug Phase]

🪲 Debug Agent: Investigating failure...
   Root cause: config: SECRET_JWT missing (confidence 0.84)
   Reproducer: tests/debug/test_repro_421.py
   Fix plan: update auth/config.py line 47

Artifacts:
  - artifacts/debug/debug_report.json
  - artifacts/debug/test_repro_421.py

✅ Debug Agent completed → Fix plan ready

🤖 Orchestrator: Debug phase completed (3.8s)
```

---

## 9. Review Phase
```
🤖 Orchestrator: Dispatching [Review Phase]

👁️ Code Review Agent: Checking policies, style, security...
   Result: APPROVE
   Notes: style ok, perf ok, security ok

Artifacts: artifacts/review/review_report.json

🤖 Orchestrator: Review phase completed (1.2s)
```

---

## 10. Meta Learning Phase
```
🤖 Orchestrator: Dispatching [Meta Learning Phase]

🧠 MetaLearning Agent: Updating policy_tweaks.json
   - Observed perf gain (p95 -32%)
   - Updated model selection rules

Artifacts:
  - ~/.smart/meta/policy_tweaks.json
  - ~/.smart/meta/prompt_recipes.json

✅ MetaLearning Agent completed
```

---

## 11. Final Summary
```
🤖 Orchestrator: All phases completed successfully 🎉
-----------------------------------------------------
Project run finished in 00:28

- Analyzer Agent: 3 warnings (see analysis_report.json)
- System Architect Agent: 3 work packages
- Code Modifier Agent: patches +26/-5 (see change_set.json)
- Testing Agent: 124/125 passed, perf p95=142ms
- Debug Agent: fixed auth config issue (SECRET_JWT)
- Code Review Agent: APPROVED
- MetaLearning Agent: policy tweaks updated

Artifacts saved to:
  ./artifacts/ (repo specific)
  ~/.smart/meta/ (global)
```

---

## 12. İnteqrasiya Qaydaları
- **Orchestrator** hər mərhələdə görünməlidir.  
- **Agent** mesajları həmişə Orchestrator-un ardınca gəlməlidir.  
- **Artifacts** hər mərhələnin sonunda göstərilməlidir.  
- **Events** vaxt damğası ilə göstərilməlidir.  
- **Final Summary** mütləq Orchestrator tərəfindən verilməlidir.  
