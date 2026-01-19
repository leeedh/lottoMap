#!/usr/bin/env python3
"""
Supabase MCP 테스트 스크립트
테이블 생성 및 INSERT 테스트를 수행합니다.
"""
import os
import sys
from pathlib import Path

# 환경변수에서 Supabase 설정 읽기
def get_supabase_config():
    """환경변수에서 Supabase 설정을 읽어옵니다."""
    config = {}
    
    # .env.local 파일 읽기 시도 (권한 문제가 있을 수 있음)
    env_file = Path(__file__).parent / '.env.local'
    if env_file.exists():
        try:
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        config[key.strip()] = value.strip().strip('"').strip("'")
        except PermissionError:
            print("⚠️ .env.local 파일 읽기 권한이 없습니다. 환경변수에서 직접 읽습니다.")
    
    # 환경변수에서 읽기 (우선순위 높음)
    supabase_url = os.getenv('SUPABASE_URL') or os.getenv('VITE_SUPABASE_URL') or config.get('SUPABASE_URL') or config.get('VITE_SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or config.get('SUPABASE_SERVICE_ROLE_KEY')
    database_url = os.getenv('DATABASE_URL') or os.getenv('SUPABASE_DB_URL') or config.get('DATABASE_URL') or config.get('SUPABASE_DB_URL')
    
    return {
        'url': supabase_url,
        'service_role_key': supabase_key,
        'database_url': database_url
    }

def execute_sql_file(file_path, config):
    """SQL 파일을 읽어서 실행합니다."""
    try:
        import psycopg2
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
        
        # Database URL을 통한 직접 연결 (DDL 실행에 적합)
        if config['database_url']:
            print(f"📌 Database URL을 사용하여 연결합니다...")
            conn = psycopg2.connect(config['database_url'])
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()
            
            # SQL 파일 읽기
            with open(file_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # SQL 실행 (세미콜론으로 구분된 여러 문장 처리)
            statements = [s.strip() for s in sql_content.split(';') if s.strip() and not s.strip().startswith('--')]
            
            for i, statement in enumerate(statements, 1):
                if statement:
                    try:
                        cursor.execute(statement)
                        print(f"✅ 문장 {i} 실행 완료")
                    except Exception as e:
                        print(f"⚠️ 문장 {i} 실행 중 오류: {e}")
                        # 일부 오류는 무시 (예: 이미 존재하는 테이블)
                        if "already exists" not in str(e).lower():
                            raise
            
            cursor.close()
            conn.close()
            print(f"✅ {file_path} 실행 완료!")
            return True
            
        else:
            print("❌ DATABASE_URL 환경변수를 찾을 수 없습니다.")
            print("\n필요한 환경변수:")
            print("  DATABASE_URL=postgresql://postgres:[PASSWORD]@[HOST]:[PORT]/postgres")
            print("\n또는 .env.local 파일에 추가:")
            print("  DATABASE_URL=postgresql://...")
            return False
            
    except ImportError as e:
        print(f"❌ 필요한 패키지가 설치되지 않았습니다: {e}")
        print("\n설치 명령어:")
        print("  pip3 install psycopg2-binary")
        print("\n또는 사용자 권한으로:")
        print("  pip3 install --user psycopg2-binary")
        return False
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """메인 함수"""
    print("=" * 60)
    print("Supabase MCP 테스트 스크립트")
    print("=" * 60)
    
    # 설정 읽기
    config = get_supabase_config()
    
    if not config['database_url'] and not (config['url'] and config['service_role_key']):
        print("\n❌ Supabase 설정이 없습니다.")
        print("\n.env.local 파일에 다음 중 하나를 추가해주세요:")
        print("  DATABASE_URL=postgresql://...")
        print("  또는")
        print("  SUPABASE_URL=https://xxx.supabase.co")
        print("  SUPABASE_SERVICE_ROLE_KEY=eyJ...")
        sys.exit(1)
    
    # SQL 파일 경로
    base_dir = Path(__file__).parent
    schema_file = base_dir / 'supabase_schema.sql'
    test_file = base_dir / 'supabase_test_insert.sql'
    
    # Step 1: 테이블 생성
    print("\n" + "=" * 60)
    print("Step 1: 테이블 생성 (DDL)")
    print("=" * 60)
    if not schema_file.exists():
        print(f"❌ 파일을 찾을 수 없습니다: {schema_file}")
        sys.exit(1)
    
    success = execute_sql_file(schema_file, config)
    if not success:
        print("❌ 테이블 생성 실패")
        sys.exit(1)
    
    # Step 2: 테스트 데이터 삽입
    print("\n" + "=" * 60)
    print("Step 2: 테스트 데이터 삽입")
    print("=" * 60)
    if not test_file.exists():
        print(f"⚠️ 테스트 파일을 찾을 수 없습니다: {test_file}")
        print("테이블 생성만 완료되었습니다.")
        sys.exit(0)
    
    success = execute_sql_file(test_file, config)
    if success:
        print("\n✅ 모든 테스트 완료!")
    else:
        print("\n⚠️ 테스트 데이터 삽입 실패 (테이블은 생성되었을 수 있음)")

if __name__ == '__main__':
    main()
