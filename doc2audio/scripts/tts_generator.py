#!/usr/bin/env python3
"""
doc2audio - 将网页文章转换为 Podcast 音频
"""

import argparse
import os
import sys

# 输出目录
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'public', 'audio')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# TTS 语音配置
VOICES = {
    'en': 'en-US-JennyNeural',
    'zh-CN': 'zh-CN-XiaoxiaoNeural',
}

# Edge TTS 最大单次处理字符数
MAX_TTS_LENGTH = 6000


def text_to_speech(text: str, voice: str, output_file: str):
    """将文字转为语音"""
    import asyncio
    import edge_tts

    async def _tts():
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_file)

    asyncio.run(_tts())


def split_text_for_tts(text: str, max_length: int = MAX_TTS_LENGTH):
    """分段处理长文本"""
    if len(text) <= max_length:
        return [text]

    # 在句号、问号、感叹号、逗号分隔处截断
    sentences = []
    current = ""
    for char in text:
        current += char
        if char in '。！？,.!?':
            sentences.append(current.strip())
            current = ""
    if current.strip():
        sentences.append(current.strip())

    # 合并段落
    segments = []
    current_segment = ""
    for sentence in sentences:
        if len(current_segment) + len(sentence) + 1 <= max_length:
            current_segment += sentence + " "
        else:
            if current_segment:
                segments.append(current_segment.strip())
            current_segment = sentence + " "
    if current_segment:
        segments.append(current_segment.strip())

    return segments


def generate_audio(text: str, voice: str, output_prefix: str, lang: str):
    """生成音频文件"""
    print(f"   语音: {voice}")

    segments = split_text_for_tts(text)
    print(f"   文本长度: {len(text)} 字符，将分 {len(segments)} 段处理")

    if len(segments) == 1:
        # 单段直接生成
        output_file = f"{output_prefix}.mp3"
        text_to_speech(text, voice, output_file)
        print(f"   ✅ 已生成: {output_file}")
        return output_file
    else:
        # 多段需要合并
        import tempfile
        import subprocess

        temp_files = []
        for i, segment in enumerate(segments):
            temp_file = f"{output_prefix}_part{i+1}.mp3"
            temp_files.append(temp_file)
            text_to_speech(segment, voice, temp_file)
            print(f"   ✅ 段 {i+1}/{len(segments)} 已生成")

        # 合并音频文件（使用 ffmpeg）
        final_file = f"{output_prefix}.mp3"
        concat_list = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
        for f in temp_files:
            concat_list.write(f"file '{os.path.abspath(f)}'\n")
        concat_list.close()

        try:
            subprocess.run([
                'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
                '-i', concat_list.name, '-c', 'copy', final_file
            ], check=True, capture_output=True)
            print(f"   ✅ 已合并: {final_file}")
        except subprocess.CalledProcessError as e:
            print(f"   ⚠️ 合并失败，保留分段文件")
            final_file = temp_files[0]

        # 清理临时文件
        for f in temp_files:
            if f != final_file and os.path.exists(f):
                os.remove(f)
        os.remove(concat_list.name)

        return final_file


def main():
    parser = argparse.ArgumentParser(description='doc2audio - Edge TTS 音频生成')
    parser.add_argument('--text', '-t', required=True, help='要转换的文字')
    parser.add_argument('--voice', '-v', default='zh-CN-XiaoxiaoNeural', help='声音名称')
    parser.add_argument('--output', '-o', help='输出文件路径')
    parser.add_argument('--lang', '-l', default='zh-CN', choices=['en', 'zh-CN'], help='语言')

    args = parser.parse_args()

    if not args.text:
        print("错误: --text 是必填参数")
        return

    # 确定输出文件
    if args.output:
        output_prefix = args.output
    else:
        import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_prefix = os.path.join(OUTPUT_DIR, f'audio-{timestamp}')

    # 生成音频
    try:
        result = generate_audio(args.text, args.voice, output_prefix, args.lang)
        print(f"\n🎉 完成！音频文件: {result}")
    except Exception as e:
        print(f"生成失败: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
