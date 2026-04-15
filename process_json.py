import json

def process_json(input_file, output_file):
    # Đọc tệp JSON gốc với encoding utf-8
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Ghi dữ liệu ra tệp mới
    # ensure_ascii=False để giữ nguyên các ký tự có dấu (Unicode)
    # indent=4 giúp tệp dễ đọc hơn
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    input_filename = 'full_result.json'
    output_filename = 'output_utf8.json'
    
    try:
        process_json(input_filename, output_filename)
        print(f"✅ Đã xử lý xong! Dữ liệu đã được lưu tại: {output_filename}")
    except FileNotFoundError:
        print(f"❌ Không tìm thấy tệp {input_filename}. Hãy đảm bảo tệp nằm cùng thư mục với script.")
    except Exception as e:
        print(f"❌ Có lỗi xảy ra: {e}")