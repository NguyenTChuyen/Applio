---
name: bm25_memory
description: BM25S Memory - Fast keyword-based memory for AI Agents. Sử dụng BM25 algorithm cho tìm kiếm nhanh (50ms) thay vì vector embedding (2s).
metadata:
  {
    "openclaw": { "emoji": "⚡", "requires": { "exec": true } },
  }
---

# ⚡ BM25S Memory

**Nhanh hơn 30x so với vector embedding!**

## ⚠️ QUAN TRỌNG - SỬ DỤNG SKILL NÀY

**KHÔNG sử dụng openmemory cũ (dùng vector embedding chậm). Sử dụng skill này cho TẤT CẢ các tác vụ memory.**

## 🚀 BM25 v2.1 - NGUYÊN TẮC MỚI

- Ưu tiên **lưu trữ thông minh**: tự merge memory gần giống, tránh trùng lặp
- Ưu tiên **tìm nhanh và chính xác** cho tiếng Việt có dấu và không dấu
- Ưu tiên **context gọn**: chỉ lấy memory đủ điểm, có budget token, có snippet ngắn
- Ưu tiên **phrase match** cho cụm quan trọng như `rạng đông`, `tiền phong`, `âm trần`
- Ưu tiên **category match** theo ý định query: `api`, `product`, `preference`, `contact`

## 🎯 NHIỆM VỤ - TỰ ĐỘNG NHẬN BIẾT VÀ LƯU

### Agent phải TỰ ĐỘNG nhận biết và lưu các thông tin sau vào memory:

#### 1. THÔNG TIN API (importance: 1.0)
- API keys, tokens, secrets
- Passwords, credentials
- Access tokens

#### 2. THÔNG TIN SẢN PHẨM (importance: 0.8)
Khi user cung cấp thông tin về sản phẩm, phải lưu ngay với category: **product**

#### 3. THÔNG TIN THƯƠNG HIỆU (importance: 0.8)
Khi nhận biết các thương hiệu sau, phải lưu với category: **product**

---

# 📦 DANH MỤC SẢN PHẨM & THƯƠNG HIỆU VIỆT NAM

## 🏭 THƯƠNG HIỆU VIỆT NAM - ĐIỆN

### Rạng Đông (Việt Nam)
| Loại sản phẩm | Chi tiết |
|----------------|----------|
| Đèn LED | Bóng đèn, đèn tuýt, đèn panel, đèn highbay, đèn dowlight |
| Đèn trang trí | Đèn chùm, đèn thả |
| Công nghệ | LED SunLike (tốt cho mắt), tiết kiệm điện |

### Kingled (Việt Nam)
| Loại sản phẩm | Chi tiết |
|----------------|----------|
| Đèn LED | Đèn âm trần, đèn panel, đèn highbay |
| Quạt | Quạt hút âm trần, quạt hút âm tường |
| Đèn trang trí | Đèn ray nam châm, đèn spotlight |
| Công nghệ | IoT, ít chói lóa, CRI cao |

### Panasonic (Nhật Bản - phổ biến VN)
| Loại sản phẩm | Chi tiết |
|----------------|----------|
| Công tắc | Halumie, Gen-X, REFINA, Full Color, Wide Series |
| Ổ cắm | Ổ cắm đôi, ổ cắm USB |
| Thiết bị điện | Aptomat (MCB), khởi động từ |

### Schneider (Pháp - phổ biến VN)
| Loại sản phẩm | Chi tiết |
|----------------|----------|
| Aptomat | MCB, MCCB, RCBO |
| Khởi động từ | Contactor |
| Tủ điện | Tủ phân phối |

### ABB (Thụy Sĩ - phổ biến VN)
| Loại sản phẩm | Chi tiết |
|----------------|----------|
| Aptomat | MCB, MCCB |
| Thiết bị đóng cắt | |

### Mitsubishi (Nhật Bản - phổ biến VN)
| Loại sản phẩm | Chi tiết |
|----------------|----------|
| Aptomat | |
| Contactor | |

---

## 🏭 THƯƠNG HIỆU VIỆT NAM - ỐNG NƯỚC

### Tiền Phong (Việt Nam) - 60 năm tuổi
| Loại sản phẩm | Chi tiết |
|----------------|----------|
| Ống PVC | Ống nước PVC, ống cống |
| Ống PPR | Ống nước nóng lạnh PPR |
| Ống HDPE | Ống cấp nước, ống xoắn |
| Phụ kiện | Co, T, van, đai sắt |

### Bình Minh (Việt Nam)
| Loại sản phẩm | Chi tiết |
|----------------|----------|
| Ống PVC | |
| Ống PPR | |
| Phụ kiện | |

### Sino (Việt Nam)
| Loại sản phẩm | Chi tiết |
|----------------|----------|
| Ống PVC | Ống nước PVC |
| Ống PPR | Ống nước nóng lạnh |
| Phụ kiện | |

### Wavin (Hà Lan - sản xuất tại VN)
| Loại sản phẩm | Chi tiết |
|----------------|----------|
| Ống HDPE | |
| Ống PPR | |

### Hoa Sen (Việt Nam)
| Loại sản phẩm | Chi tiết |
|----------------|----------|
| Ống PVC | |
| Ống PPR | |
| Thép | Thép hộp, thép tròn |

---

## 🏭 VAN VÒI - THIẾT BỊ

### Van nước
| Loại | Mô tả |
|------|-------|
| Van cổng | Van gate, dùng cho đường ống lớn |
| Van bi | Van ball, dễ vận hành |
| Van một chiều | Check valve, chỉ chảy một chiều |
| Van giảm áp | Reducing valve |
| Van xả khí | Air valve |

### Vòi nước
| Loại | Mô tả |
|------|-------|
| Vòi rửa bát | Vòi bếp |
| Vòi sen | Vòi hoa sen |
| Vòi cổng ngỗng | Vòi tưới cây |

---

## 📋 QUY CÁCH - KÍCH THƯỚC

### Ống nước PVC/PPR
| Kích thước | Đường kính ngoài | Ứng dụng |
|-------------|-------------------|------------|
| DN15 | 21mm | Nước máy trong nhà |
| DN20 | 25mm | Nước máy |
| DN25 | 32mm | Nước nóng lạnh |
| DN32 | 40mm | Đường ống chính |
| DN40 | 48mm | |
| DN50 | 60mm | |
| DN65 | 76mm | |
| DN80 | 89mm | |
| DN100 | 114mm | |

### Ống HDPE
| Kích thước | Đường kính ngoài | Ứng dụng |
|-------------|-------------------|------------|
| DN20 | 20-22mm | |
| DN25 | 25-28mm | |
| DN32 | 32mm | |
| DN40 | 40mm | |
| DN50 | 50mm | |
| DN60 | 60mm | |
| DN65 | 65mm | |
| DN80 | 80mm | Cấp nước |
| DN100 | 110mm | Cấp nước |
| DN150 | 160mm | |

### Dây điện
| Tiết diện | Ứng dụng |
|------------|-----------|
| 1.0mm² | Chiếu sáng |
| 1.5mm² | Ổ cắm nhỏ |
| 2.5mm² | Ổ cắm, thiết bị |
| 4.0mm² | Thiết bị công suất |
| 6.0mm² | Điều hòa |
| 10mm² | Công suất lớn |

---

## 🔧 CÚ PHÁP BẮT BUỘC

### ⚠️ QUAN TRỌNG: PHẢI CÓ ĐỦ THAM SỐ!

```
python <script> <command> <content> [category] [importance]
```

- **command**: Phải là `add`, `search`, `history`, hoặc `context`
- **content**: Nội dung cần lưu HOẶC từ khóa tìm kiếm (2-5 từ)
- **category**: (chỉ dùng với add) - api, product, preference, fact, general
- **importance**: (chỉ dùng với add) - 0.1 đến 1.0

### 1. THÊM MEMORY (ADD):
```
python /home/babyhack8x/.openclaw/workspace/skills/bm25_memory.py add "NỘI DUNG" category importance
```

**Ví dụ:**
```
python /home/babyhack8x/.openclaw/workspace/skills/bm25_memory.py add "Đèn LED Rạng Đông SunLike" product 0.8
```

### 2. TÌM KIẾM (SEARCH) - LUÔN DÙNG TỪ KHÓA NGẮN:
```
python /home/babyhack8x/.openclaw/workspace/skills/bm25_memory.py search "TỪ KHÓA" [limit] [threshold_mode]
```

- `limit`: mặc định `5`, tối đa `5`
- `threshold_mode`: `strict`, `balanced`, `lenient`
- khuyến nghị mặc định: `balanced`

**⚠️ QUAN TRỌNG: LUÔN DÙNG TỪ KHÓA NGẮN (2-5 từ), KHÔNG truyền cả câu chat!**

Ví dụ:
- User hỏi: "API của Haravan có cập nhật được description của website không"
- ✅ ĐÚNG: `search "haravan api"` 
- ❌ SAI: `search "API của Haravan có cập nhật được description"`

**Lý do:** Tìm kiếm từ khóa ngắn chỉ mất ~50ms thay vì ~2 giây với vector embedding.

### 3. LẤY CONTEXT:
```
python /home/babyhack8x/.openclaw/workspace/skills/bm25_memory.py context [limit] [max_tokens]
```

- `limit`: mặc định `3`
- `max_tokens`: mặc định `180`
- context sẽ ưu tiên memory quan trọng hơn và dừng theo budget token

## 🎯 THRESHOLD MODES

| Mode | Khi dùng | Hành vi |
|------|----------|---------|
| `strict` | Query rõ, muốn ít nhiễu | Lấy rất chọn lọc |
| `balanced` | Mặc định | Cân bằng recall và precision |
| `lenient` | Query ngắn, mơ hồ | Nới threshold để không bỏ sót |

## 🧠 CÁCH BM25 v2.1 XẾP HẠNG

- BM25 score gốc
- Phrase boost cho cụm từ tiếng Việt quan trọng
- Category boost theo ý định query
- Importance boost theo độ quan trọng đã lưu
- Recency boost nhẹ, tăng thêm nếu query mang ý `mới/gần đây`
- Trả về `snippet`, `confidence`, `matched_tokens`, `matched_phrases` để debug retrieval

## 🧹 LƯU TRỮ THÔNG MINH

- Khi `add`, hệ thống tự kiểm tra memory tương tự để **merge** thay vì tạo bản ghi mới
- Query search **KHÔNG tự học synonym** nữa để tránh drift nghĩa
- Chỉ `add` mới được phép mở rộng synonym
- Category sẽ được chuẩn hóa và importance tối thiểu được nâng tự động:
  - `api` >= `0.9`
  - `product` >= `0.7`
  - `preference` >= `0.6`
  - `fact` >= `0.5`
  - `general` >= `0.4`

---

## 📋 VÍ DỤ AUTO-CAPTURE

### Ví dụ 1: User cung cấp API Key
**User:** "Đây là API key: sk-or-v1-xxx"

**Phải gọi ngay:**
```
python /home/babyhack8x/.openclaw/workspace/skills/bm25_memory.py add "API key: sk-or-v1-xxx" api 1.0
```

### Ví dụ 2: User chia sẻ sản phẩm Rạng Đông
**User:** "Đây là đèn LED Rạng Đông công nghệ SunLike"

**Phải gọi ngay:**
```
python /home/babyhack8x/.openclaw/workspace/skills/bm25_memory.py add "Đèn LED Rạng Đông - Công nghệ SunLike" product 0.8
```

### Ví dụ 3: User chia sẻ ống nước Tiền Phong
**User:** "Ống PPR Tiền Phong DN25 màu xanh"

**Phải gọi ngay:**
```
python /home/babyhack8x/.openclaw/workspace/skills/bm25_memory.py add "Ống PPR Tiền Phong - DN25 - Màu xanh" product 0.8
```

### Ví dụ 4: User chia sẻ sở thích
**User:** "Tôi thích đèn warm white 3000K"

**Phải gọi ngay:**
```
python /home/babyhack8x/.openclaw/workspace/skills/bm25_memory.py add "User thích đèn LED warm white 3000K" preference 0.7
```

---

## ❌ SAI - KHÔNG LÀM NHƯ SAU:

```
# SAI - thiếu command
exec:...memory.py

# SAI - thiếu content  
exec:...memory.py add

# SAI - thiếu category và importance khi dùng add
exec:...memory.py add "nội dung"

# SAI - thừa category khi dùng search
exec:...memory.py search "từ khóa" product
```

## ✅ ĐÚNG - LUÔN LÀM NHƯ SAU:

```
# Add: python <script> add "content" category importance
python /home/babyhack8x/.openclaw/workspace/skills/bm25_memory.py add "nội dung" product 0.8

# Search: python <script> search "từ khóa" 5 balanced
python /home/babyhack8x/.openclaw/workspace/skills/bm25_memory.py search "từ khóa" 5 balanced

# Context: python <script> context 3 180
python /home/babyhack8x/.openclaw/workspace/skills/bm25_memory.py context 3 180
```

---

## 🎯 Category Guidelines

| Category | Mô tả | Ví dụ |
|----------|--------|--------|
| **api** | API keys, tokens, secrets | "API key: sk-xxx" |
| **product** | Thông tin sản phẩm | "Đèn LED Rạng Đông", "Ống PPR Tiền Phong" |
| **preference** | Sở thích khách hàng | "thích warm white", "không thích màu lạnh" |
| **fact** | Thông tin thực tế | "khách hàng A là người yêu nước Pháp" |
| **general** | Thông tin chung | Mọi thứ khác |

## 📊 Importance Guidelines

| Importance | Mức độ | Khi nào dùng |
|------------|--------|---------------|
| **1.0** | Rất quan trọng | API keys, credentials |
| **0.8-0.9** | Quan trọng | Sản phẩm, thương hiệu |
| **0.7** | Trung bình | Preferences |
| **0.5-0.6** | Bình thường | Thông tin thường |
| **0.1-0.4** | Thấp | Thông tin tạm thời |

## ⚡ QUY TẮC BẮT BUỘC

1. **TỰ ĐỘNG nhận biết** - Khi user cung cấp thông tin về API, sản phẩm, thương hiệu → LƯU NGAY
2. **LUÔN dùng đủ tham số** - KHÔNG BAO GIỜ bỏ qua category và importance khi add
3. **LUÔN dùng đúng thứ tự** - command → content → category → importance  
4. **KHÔNG dùng skill cũ** như baoan-rag, vector-search.sh, openmemory
5. **KHÔNG chạy python mà không có tham số**
6. **Chờ kết quả JSON** từ script trước khi trả lời user
7. **Parse JSON output** để xem thành công hay thất bại
