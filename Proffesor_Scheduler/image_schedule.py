import csv
import pandas as pd
import re
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from collections import defaultdict
import numpy as np

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

def parse_time(time_str):
    """시간 문자열을 파싱하여 요일과 시간을 추출"""
    if not time_str or pd.isna(time_str) or str(time_str).strip() == '':
        return []
    
    # 요일 매핑
    day_map = {'월': 0, '화': 1, '수': 2, '목': 3, '금': 4, '토': 5, '일': 6}
    
    schedule = []
    # 요일(시간~시간) 형태로 파싱
    pattern = r'([월화수목금토일])\((\d{2}:\d{2})~(\d{2}:\d{2})\)'
    matches = re.findall(pattern, str(time_str))
    
    for day, start_time, end_time in matches:
        schedule.append({
            'day': day_map.get(day, -1),
            'day_name': day,
            'start': start_time,
            'end': end_time
        })
    
    return schedule

def time_to_minutes(time_str):
    """시간 문자열을 분으로 변환"""
    hour, minute = map(int, time_str.split(':'))
    return hour * 60 + minute

def create_image_schedule(csv_file, professor_name=None, selected_majors=None, major_display=None, save_path=None):
    # CSV 파일 읽기
    df = pd.read_csv(csv_file, encoding='utf-8-sig')
    
    if professor_name and selected_majors:
        # 특정 교수의 특정 학과 강의만 필터링
        condition = (df['professor'].notna() & 
                    df['professor'].astype(str).str.contains(professor_name, na=False, regex=False) &
                    df['major'].notna())
        
        # 선택된 학과들 중 하나라도 포함되는 경우
        major_condition = False
        for major in selected_majors:
            major_condition |= df['major'].astype(str).str.contains(major, na=False, regex=False)
        
        condition &= major_condition
        df = df[condition]
        
        if df.empty:
            print(f"{professor_name} 교수의 선택된 학과 강의를 찾을 수 없습니다.")
            return
    elif professor_name:
        # 특정 교수의 모든 강의
        df = df[df['professor'].notna() & df['professor'].astype(str).str.contains(professor_name, na=False, regex=False)]
        if df.empty:
            print(f"{professor_name} 교수의 강의를 찾을 수 없습니다.")
            return
    
    # 시간표 설정
    days = ['월', '화', '수', '목', '금', '토']
    
    # 실제 강의 시간을 분석하여 시간 범위 결정
    min_start_hour = 24
    max_end_hour = 0
    has_classes = False
    
    # 모든 강의의 시간을 확인하여 범위 조정
    for _, row in df.iterrows():
        time_info = parse_time(row['time'])
        for time_slot in time_info:
            if time_slot['start'] and time_slot['end']:
                has_classes = True
                start_hour_val = int(time_slot['start'].split(':')[0])
                end_hour_val = int(time_slot['end'].split(':')[0])
                end_minute = int(time_slot['end'].split(':')[1])
                
                # 분이 0이 아니면 다음 시간대까지 포함
                if end_minute > 0:
                    end_hour_val += 1
                
                # 시간 범위 확장
                min_start_hour = min(min_start_hour, start_hour_val)
                max_end_hour = max(max_end_hour, end_hour_val)
    
    # 강의가 없거나 범위가 너무 좁으면 기본값 사용
    if not has_classes or max_end_hour - min_start_hour < 6:
        if not has_classes:
            # 강의가 없으면 기본 9-15시 (6시간)
            start_hour = 9
            end_hour = 15
        else:
            # 강의가 있지만 범위가 좁으면 6시간으로 확장
            center_time = (min_start_hour + max_end_hour) / 2
            start_hour = max(6, int(center_time - 3))  # 최소 6시부터
            end_hour = start_hour + 6
    else:
        # 양쪽에 1시간씩 여유 추가
        start_hour = max(6, min_start_hour - 1)  # 최소 6시부터
        end_hour = min(24, max_end_hour + 1)     # 최대 24시까지
    
    # 그래프 설정 (시간 범위에 따라 크기 조정)
    time_range = end_hour - start_hour
    width = 16  # 고정 폭
    height = max(8, time_range * 1.2)  # 시간당 1.2의 높이, 최소 8
    fig, ax = plt.subplots(figsize=(width, height))
    
    # 시간표 그리드 그리기 (강의 블록보다 뒤에 그려지도록)
    for i in range(len(days) + 1):
        ax.axvline(x=i, color='black', linewidth=1, zorder=1)
    
    for i in range((end_hour - start_hour) * 2 + 1):  # 30분 단위
        ax.axhline(y=i, color='black', linewidth=0.5, zorder=1)
    
    # 요일 헤더
    for i, day in enumerate(days):
        ax.text(i + 0.5, (end_hour - start_hour) * 2 , day, 
                ha='center', va='bottom', fontsize=14, fontweight='bold')
    
    # 시간 레이블
    for i in range(end_hour - start_hour + 1):
        hour = start_hour + i
        ax.text(-0.1, (end_hour - start_hour) * 2 - i * 2, f'{hour:02d}:00', 
                ha='right', va='center', fontsize=10)
        if i < end_hour - start_hour:
            ax.text(-0.1, (end_hour - start_hour) * 2 - i * 2 - 1, f'{hour:02d}:30', 
                    ha='right', va='center', fontsize=9, alpha=0.7)
    
    # 색상 팔레트
    colors = ['#FFE5B4', '#FFCCCC', '#CCE5FF', '#E5CCFF', '#CCFFCC', '#FFCC99', 
              '#F0E68C', '#DDA0DD', '#98FB98', '#F0E68C', '#87CEEB', '#DEB887']
    
    course_colors = {}
    color_idx = 0
    
    # 강의 정보 배치
    for _, row in df.iterrows():
        professor = str(row['professor']).strip() if pd.notna(row['professor']) else ''
        course_name = str(row['couse_name']).strip() if pd.notna(row['couse_name']) else ''
        course_code = str(row['course_code']).strip() if pd.notna(row['course_code']) else ''
        
        # 강의명에서 [학사], [전선] 등의 태그 제거
        course_name = re.sub(r'\[.*?\]', '', course_name).strip()
        
        if not professor or not course_name:
            continue
            
        time_info = parse_time(row['time'])
        
        # 강의별 고유 색상 할당
        course_key = f"{course_name}_{professor}"
        if course_key not in course_colors:
            course_colors[course_key] = colors[color_idx % len(colors)]
            color_idx += 1
        
        for time_slot in time_info:
            day_idx = time_slot['day']
            if day_idx < 0 or day_idx >= len(days):
                continue
                
            start_minutes = time_to_minutes(time_slot['start'])
            end_minutes = time_to_minutes(time_slot['end'])
            
            # 9시 기준으로 위치 계산 (30분 단위)
            start_pos = ((start_minutes - start_hour * 60) / 30)
            duration = (end_minutes - start_minutes) / 30
            
            # 시간표 범위 내에 있는지 확인
            if start_minutes >= start_hour * 60 and end_minutes <= end_hour * 60:
                # 강의 블록 그리기 (배경선을 가리도록)
                y_pos = (end_hour - start_hour) * 2 - start_pos - duration
                rect = patches.Rectangle((day_idx + 0.01, y_pos + 0.01), 
                                       0.98, duration - 0.02,
                                       linewidth=1, 
                                       edgecolor='black',
                                       facecolor=course_colors[course_key],
                                       alpha=1.0,  # 완전 불투명하게 해서 뒤의 격자선을 가림
                                       zorder=10)  # 격자선보다 위에 그리기
                ax.add_patch(rect)
                
                # 강의명만 표시
                text_y = y_pos + duration / 2
                
                # 띄어쓰기를 개행으로 변경하고, 네 글자 이상 연속되면 개행 추가
                course_display = course_name.replace(' ', '\n')
                
                # 각 줄에서 네 글자 이상 연속되는 부분을 찾아서 개행 추가
                lines = course_display.split('\n')
                processed_lines = []
                
                for line in lines:
                    if len(line) > 4:
                        # 네 글자씩 나누어 개행 추가
                        chunks = []
                        for i in range(0, len(line), 4):
                            chunks.append(line[i:i+4])
                        processed_lines.extend(chunks)
                    else:
                        processed_lines.append(line)
                
                course_display = '\n'.join(processed_lines)
                
                # 줄 수에 따른 텍스트 위치 조정
                line_count = course_display.count('\n') + 1
                line_height = 0.15
                start_y = text_y + (line_count - 1) * line_height / 2
                
                ax.text(day_idx + 0.5, start_y, course_display,
                        ha='center', va='center', fontsize=9, fontweight='bold',
                        linespacing=1.2, zorder=15)  # 텍스트를 가장 위에 표시
    
    # 축 설정
    ax.set_xlim(0, len(days))
    ax.set_ylim(0, (end_hour - start_hour) * 2)
    ax.set_aspect('equal')
    
    # 축 숨기기
    ax.set_xticks([])
    ax.set_yticks([])
    
    # 제목
    if professor_name:
        title = f'{professor_name} 교수 시간표'
    else:
        title = '전체 교수 시간표'
    
    plt.title(title, fontsize=16, fontweight='bold', pad=20)
    
    # 레이아웃 조정
    plt.tight_layout()
    
    # 저장
    if save_path:
        filename = save_path
    else:
        if professor_name and major_display:
            filename = f'{major_display}_시간표.png'.replace('/', '_').replace('\\', '_').replace('(', '').replace(')', '').replace(':', '').replace(',', '_')
        elif professor_name:
            filename = f'{professor_name}_시간표.png'.replace('/', '_').replace('\\', '_')
        else:
            filename = '전체_시간표.png'
    
    plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"시간표 이미지가 '{filename}'로 저장되었습니다.")
    
    # 이미지 표시
    plt.show()
    
    return filename

def list_all_professors(csv_file):
    """모든 교수 목록 출력"""
    df = pd.read_csv(csv_file, encoding='utf-8-sig')
    professors = df['professor'].dropna().astype(str)
    professors = [p.strip() for p in professors if p.strip() and p.strip() != 'nan']
    
    print("=== 교수 목록 ===")
    unique_professors = sorted(set(professors))
    for prof in unique_professors:
        print(f"- {prof}")
    return unique_professors

def get_professor_majors(csv_file, professor_name):
    """특정 교수가 담당하는 강의들의 학과 목록 반환"""
    df = pd.read_csv(csv_file, encoding='utf-8-sig')
    
    # 해당 교수의 강의들 필터링
    prof_courses = df[df['professor'].notna() & 
                     df['professor'].astype(str).str.contains(professor_name, na=False, regex=False)]
    
    if prof_courses.empty:
        return []
    
    # 학과 목록 추출
    majors = prof_courses['major'].dropna().astype(str)
    majors = [m.strip() for m in majors if m.strip() and m.strip() != 'nan']
    
    return sorted(set(majors))

def select_professor_and_majors(csv_file):
    """교수를 선택하고 해당 교수의 학과들을 선택"""
    # CSV 파일에서 교수 목록 가져오기 (출력하지 않음)
    df = pd.read_csv(csv_file, encoding='utf-8-sig')
    professors = df['professor'].dropna().astype(str)
    professors = [p.strip() for p in professors if p.strip() and p.strip() != 'nan']
    professors = sorted(set(professors))
    
    print(f"교수 이름을 입력하세요 (부분 일치 가능, 전체: 'all'):")
    choice = input("선택: ").strip()
    
    if choice.lower() == 'all':
        return None, None, "전체"
    
    selected_professor = None
    
    # 입력한 이름이 포함된 교수 찾기
    matching_profs = [p for p in professors if choice in p]
    if len(matching_profs) == 1:
        selected_professor = matching_profs[0]
    elif len(matching_profs) > 1:
        print(f"\n'{choice}'가 포함된 교수들:")
        for i, prof in enumerate(matching_profs, 1):
            print(f"{i}. {prof}")
        
        sub_choice = input("번호를 선택하세요: ").strip()
        if sub_choice.isdigit():
            sub_num = int(sub_choice)
            if 1 <= sub_num <= len(matching_profs):
                selected_professor = matching_profs[sub_num - 1]
    else:
        # 정확히 일치하는 교수가 있는지 확인
        exact_match = [p for p in professors if p == choice]
        if exact_match:
            selected_professor = exact_match[0]
        else:
            print(f"'{choice}'와 일치하는 교수를 찾을 수 없습니다.")
            return None, None, None
    
    # 2단계: 해당 교수의 학과들 조회
    professor_majors = get_professor_majors(csv_file, selected_professor)
    
    if not professor_majors:
        print(f"{selected_professor} 교수의 강의를 찾을 수 없습니다.")
        return None, None, None
    
    print(f"\n{selected_professor} 교수가 담당하는 강의의 학과들:")
    for i, major in enumerate(professor_majors, 1):
        print(f"{i}. {major}")
    
    print(f"\n포함할 학과를 선택하세요 (번호 입력, 여러 개 선택시 쉼표로 구분, 전체: 'all'):")
    major_choice = input("선택: ").strip()
    
    if major_choice.lower() == 'all':
        selected_majors = professor_majors
        major_display = f"{selected_professor} (전체 학과)"
    else:
        try:
            # 쉼표로 구분된 번호들 처리
            choices = [int(x.strip()) for x in major_choice.split(',')]
            selected_majors = []
            
            for choice_num in choices:
                if 1 <= choice_num <= len(professor_majors):
                    selected_majors.append(professor_majors[choice_num - 1])
            
            if not selected_majors:
                print("잘못된 선택입니다.")
                return None, None, None
                
            major_display = f"{selected_professor} ({', '.join(selected_majors)})"
            
        except ValueError:
            print("잘못된 입력입니다.")
            return None, None, None
    
    return selected_professor, selected_majors, major_display

if __name__ == "__main__":
    csv_file = "courses.csv"
    
    # 교수 선택 및 학과 선택
    professor_name, selected_majors, major_display = select_professor_and_majors(csv_file)
    
    if professor_name is None and major_display is None:
        print("프로그램을 종료합니다.")
        exit()
    
    if professor_name is None and major_display == "전체":
        # 전체 교수 시간표
        create_image_schedule(csv_file)
    else:
        # 선택된 교수의 선택된 학과 시간표
        create_image_schedule(csv_file, professor_name, selected_majors, major_display)
