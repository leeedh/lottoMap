#!/bin/bash
# 로또 자동 갱신 실행 스크립트
# Cron이나 수동 실행 시 사용

cd /Users/ldh/Projects/lotto-crawling
source venv/bin/activate

# 로그 파일에 기록
LOG_FILE="auto_update.log"
echo "" >> $LOG_FILE
echo "========================================" >> $LOG_FILE
echo "실행 시간: $(date '+%Y-%m-%d %H:%M:%S')" >> $LOG_FILE
echo "========================================" >> $LOG_FILE

# 자동 갱신 실행
python auto_update.py 2>&1 | tee -a $LOG_FILE

echo "완료: $(date '+%Y-%m-%d %H:%M:%S')" >> $LOG_FILE
