# Harness library

Harness²의 경험 라이브러리 자리다(논문 2.3절, 저장소 `harness2/core/library.py`). 아직 항목은 없다. 항목은 실제 실행에서 대조 근거가 있을 때만 넣는다.

```
project/harness/library/
  <domain>/                    # architecture, ux-product, photography ...
    INDEX.md                   # 모든 항목 목록. 디스크에서 다시 만든다
    harnesses/<task>/
      harness/                 # 채택한 하네스 트리 전체 (실행 가능한 파일 그대로, 요약하지 않는다)
      EXPERIENCE.md            # 왜 채택했나
```

`EXPERIENCE.md`의 항목(Harness² 저장소와 같다):

- `adopted`: 채택한 후보와 실행 ID
- `components`: 어떤 구성요소가 들어 있나
- `## Why this was chosen`
- `## What each edit did`
- `## Transferable lesson`: `cue`(언제 해당하나), `lesson`, `evidence`, `confidence`

규칙:

- 근거가 부족하면 항목을 넣지 않는다.
- 채점 결과, 루브릭 답, 점수, 블라인드 키가 들어 있는 트리는 넣지 않는다. `agents/baseAgent/scripts/check_base.py`의 표식 검사와 같은 기준이다.
- 도메인별로 따로 쌓는다. 같은 도메인의 다음 과제가 앞 항목을 읽는다.
