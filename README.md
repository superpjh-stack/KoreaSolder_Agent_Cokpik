# 고려솔더 AI Agent Cockpit

고려솔더의 원료 LOT, 수입검사, 용해 배치, 주조·압연, 품질검사, 포장과 출하를 하나의 읽기 전용 업무 화면으로 연결한 Streamlit 시제품이다.

초기 DB와 지식문서는 모두 `데모·미승인` 가상 데이터다. 실제 합금 조성, 배합비, 온도·시간·치수 공차는 승인 문서가 등록되기 전까지 답변하지 않는다. 공개 기업 정보는 화면의 회사 맥락을 정하는 데만 사용했으며 생산 기준의 근거로 사용하지 않았다.

## 실행

```bash
pip install -r requirements.txt
streamlit run app.py
```

PostgreSQL + pgvector는 `docker compose up --build`로 시작한다. `DATABASE_URL`이 없으면 `goryeo_solder_demo.db` SQLite로 자동 전환한다. OpenAI 키가 없을 때도 DB·문서 조회 화면은 동작한다.
