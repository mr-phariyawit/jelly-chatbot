# AI Support Assistant - Constitution

## Core Principles

### I. AI-First User Experience
ทุก interaction ต้องผ่าน AI ก่อน เพื่อช่วย triage และแก้ปัญหาเบื้องต้น ก่อนส่งต่อเจ้าหน้าที่
- AI ต้องเข้าใจภาษาธรรมชาติ (ไทย/อังกฤษ)
- รองรับ Multi-modal input (text, image)
- ตอบกลับภายใน 3 วินาที

### II. Knowledge-Driven Resolution
ทุกคำตอบต้องอ้างอิงจาก Knowledge Base ที่ verified
- ใช้ Historical Incident Data (950+ cases)
- User Manuals เป็น Single Source of Truth
- No hallucination - ถ้าไม่รู้ต้องบอกตรงๆ

### III. Auto-Documentation
ทุก interaction สร้าง record อัตโนมัติ
- Auto Ticket Creation จาก conversation
- Structured data extraction
- Audit trail สำหรับทุก case

### IV. Human-in-the-Loop
AI ช่วย แต่คนตัดสินใจสุดท้าย
- Escalation path ชัดเจน
- ปุ่มส่งต่อเจ้าหน้าที่ในทุก stage
- AI รวบรวมข้อมูลให้ครบก่อนส่งต่อ

### V. Privacy by Design
ปกป้องข้อมูลส่วนบุคคล
- Mask sensitive data (เลขบัตร, เบอร์โทร)
- Role-based access control
- Audit logs for compliance

## Technical Constraints

### Supported Systems (12 Apps)
- JDID EKYC, JMB_CRM, JAS_CRM, SGF+
- ONE ID, JOIN, PAH Advance, CASA_CRM
- Baanbaan, JAII DEE, Teenoi, J Wallet

### Default Categories
- ปัญหาแอพ, ปัญหาบัตรประชาชน, ปัญหาอุปกรณ์
- Register JDIDeKYC, KYC, OTP, Information
- Change info, coupon, Seed Phrase, J Wallet

### Escalation Channels
- J Point → CRM issues
- SG → SGF+ issues
- Infra Team → Technical issues

## Quality Gates

### Before Deployment
- [ ] AI accuracy ≥ 85% on test cases
- [ ] Response time < 3 seconds
- [ ] Knowledge Base coverage ≥ 90% of Top 20 issues

### Monitoring
- User satisfaction score
- Resolution time trends
- Escalation rate

## Governance

Constitution supersedes all other practices. Amendments require:
1. Documentation update
2. Team approval
3. Deployment plan

**Version**: 1.0.0 | **Ratified**: 2026-01-07 | **Last Amended**: 2026-01-07
