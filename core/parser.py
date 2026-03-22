"""CGATS 파일 파서 모듈

I1Pro3 측정 데이터(CGATS 형식) txt 파일을 파싱하여
L*a*b* 및 기타 측정 데이터를 추출합니다.
"""

import pandas as pd
import re
from typing import Tuple


def parse_cgats_string(content: str) -> Tuple[pd.DataFrame, dict]:
    """CGATS 형식 문자열을 파싱하여 DataFrame과 메타데이터를 반환합니다.

    Args:
        content: CGATS 형식의 문자열

    Returns:
        (DataFrame, metadata_dict) 튜플

    Raises:
        ValueError: 파싱 실패 시
    """
    lines = content.strip().split('\n')
    metadata = {}
    columns = []
    data_lines = []
    in_data_format = False
    in_data = False

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if line.startswith('CGATS'):
            metadata['FORMAT'] = line
            continue

        if line.startswith('ORIGINATOR'):
            match = re.search(r'"([^"]*)"', line)
            metadata['ORIGINATOR'] = match.group(1) if match else line.split(None, 1)[1]
            continue

        if line.startswith('DESCRIPTOR'):
            match = re.search(r'"([^"]*)"', line)
            metadata['DESCRIPTOR'] = match.group(1) if match else line.split(None, 1)[1]
            continue

        if line.startswith('NUMBER_OF_FIELDS'):
            metadata['NUMBER_OF_FIELDS'] = int(line.split()[1])
            continue

        if line.startswith('NUMBER_OF_SETS'):
            metadata['NUMBER_OF_SETS'] = int(line.split()[1])
            continue

        if line == 'BEGIN_DATA_FORMAT':
            in_data_format = True
            continue

        if line == 'END_DATA_FORMAT':
            in_data_format = False
            continue

        if line == 'BEGIN_DATA':
            in_data = True
            continue

        if line == 'END_DATA':
            in_data = False
            continue

        if in_data_format:
            columns.extend(line.split())
            continue

        if in_data:
            parts = []
            current = line
            while current:
                current = current.strip()
                if not current:
                    break
                if current.startswith('"'):
                    end_idx = current.index('"', 1)
                    parts.append(current[1:end_idx])
                    current = current[end_idx + 1:]
                else:
                    token = current.split(None, 1)
                    parts.append(token[0])
                    current = token[1] if len(token) > 1 else ''
            data_lines.append(parts)

    if not columns:
        raise ValueError("데이터 형식(DATA_FORMAT)을 찾을 수 없습니다.")

    if not data_lines:
        raise ValueError("측정 데이터(DATA)를 찾을 수 없습니다.")

    df = pd.DataFrame(data_lines, columns=columns[:len(data_lines[0])])

    for col in df.columns:
        if col in ('SAMPLE_NAME', 'NAME'):
            continue
        try:
            df[col] = pd.to_numeric(df[col])
        except (ValueError, TypeError):
            pass

    metadata['COLUMNS'] = columns
    metadata['SAMPLE_COUNT'] = len(df)

    return df, metadata


def parse_cgats_file(file_obj) -> Tuple[pd.DataFrame, dict]:
    """업로드된 파일 객체 또는 파일 경로를 파싱합니다.

    Args:
        file_obj: Streamlit UploadedFile 또는 파일 경로 문자열

    Returns:
        (DataFrame, metadata_dict) 튜플

    Raises:
        ValueError: 파싱 실패 시
    """
    if isinstance(file_obj, str):
        with open(file_obj, 'r', encoding='utf-8') as f:
            content = f.read()
    else:
        content = file_obj.read()
        if isinstance(content, bytes):
            content = content.decode('utf-8')

    return parse_cgats_string(content)


# ---------------------------------------------------------------------------
# 하위 호환 별칭 및 유틸리티
# ---------------------------------------------------------------------------

class CGATSParseError(ValueError):
    """CGATS 파싱 에러."""
    pass


def spectral_wavelengths(df: pd.DataFrame) -> list:
    """DataFrame에서 스펙트럼 파장 값 목록을 추출합니다.

    SPECTRAL_380, SPECTRAL_390, ... 또는 SPEC_380, nm380 등의 컬럼에서
    파장 숫자를 추출하여 정렬된 리스트로 반환합니다.
    스펙트럼 컬럼이 없으면 빈 리스트를 반환합니다.
    """
    import re as _re
    wavelengths = []
    for col in df.columns:
        m = _re.search(r'(?:SPECTRAL_|SPEC_|nm)(\d+)', col, _re.IGNORECASE)
        if m:
            wavelengths.append(int(m.group(1)))
    return sorted(wavelengths)


def parse_cgats(content_or_file) -> Tuple[pd.DataFrame, dict]:
    """parse_cgats_string / parse_cgats_file 통합 래퍼."""
    if isinstance(content_or_file, str) and '\n' in content_or_file:
        return parse_cgats_string(content_or_file)
    return parse_cgats_file(content_or_file)


def parse_multiple(file_list) -> Tuple[pd.DataFrame, list]:
    """여러 파일을 파싱하여 하나의 DataFrame으로 합칩니다."""
    all_dfs = []
    all_meta = []
    for f in file_list:
        df, meta = parse_cgats_file(f)
        name = f if isinstance(f, str) else getattr(f, 'name', 'unknown')
        df['SOURCE_FILE'] = name
        all_dfs.append(df)
        all_meta.append(meta)
    combined = pd.concat(all_dfs, ignore_index=True) if all_dfs else pd.DataFrame()
    return combined, all_meta


def get_lab(df: pd.DataFrame):
    """DataFrame에서 L*, a*, b* 컬럼을 추출합니다."""
    lab_map = {}
    for col in df.columns:
        upper = col.upper()
        if upper in ('LAB_L', 'L*', 'L'):
            lab_map['L'] = col
        elif upper in ('LAB_A', 'A*', 'A'):
            lab_map['a'] = col
        elif upper in ('LAB_B', 'B*', 'B'):
            lab_map['b'] = col
    if len(lab_map) == 3:
        return df[[lab_map['L'], lab_map['a'], lab_map['b']]].copy()
    return None


def get_spectral(df: pd.DataFrame):
    """DataFrame에서 스펙트럼 데이터 컬럼을 추출합니다."""
    spec_cols = [c for c in df.columns if c.startswith('SPECTRAL_') or c.startswith('nm')]
    if spec_cols:
        return df[spec_cols].copy()
    return None
