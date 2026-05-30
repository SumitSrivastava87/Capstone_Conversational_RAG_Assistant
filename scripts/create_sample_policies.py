"""
Generates sample policy PDFs for all 5 intent namespaces.
Run once to seed the vector store before starting the server.
"""

from pathlib import Path
from fpdf import FPDF

OUT_DIR = Path("data/policies")
OUT_DIR.mkdir(parents=True, exist_ok=True)

POLICIES = {
    "complaint": {
        "filename": "complaint_policy.pdf",
        "title": "Customer Complaint Handling Policy",
        "sections": [
            ("Purpose", (
                "This policy sets out how we handle customer complaints fairly, "
                "consistently, and promptly. All complaints are taken seriously and "
                "treated as an opportunity to improve our products and services."
            )),
            ("Scope", (
                "This policy applies to all complaints received via any channel: "
                "email, phone, live chat, social media, or in-store."
            )),
            ("Definition of a Complaint", (
                "A complaint is any expression of dissatisfaction, whether justified "
                "or not, about our products, services, staff, or complaint-handling "
                "process itself."
            )),
            ("Acknowledgement", (
                "We will acknowledge all complaints within 1 business day. "
                "For complaints received outside business hours, acknowledgement "
                "will be sent on the next business day."
            )),
            ("Investigation & Resolution", (
                "We aim to resolve all complaints within 5 business days. "
                "Complex complaints may take up to 15 business days. "
                "The customer will be kept informed of progress throughout. "
                "A named case handler will be assigned to every complaint."
            )),
            ("Compensation", (
                "Where a complaint is upheld, we may offer one or more of the following: "
                "a full or partial refund, a replacement product, store credit, "
                "a written apology, or a goodwill gesture appropriate to the severity."
            )),
            ("Damaged or Faulty Goods", (
                "If a product arrives damaged or develops a fault within 30 days of "
                "purchase, the customer is entitled to a full refund or free replacement "
                "at their choice. Photographic evidence may be requested to expedite the claim."
            )),
            ("Escalation", (
                "If a customer is not satisfied with the initial resolution, the complaint "
                "may be escalated to a senior customer service manager within 3 business days. "
                "The customer will receive a final written response within 5 business days of escalation."
            )),
            ("Record Keeping", (
                "All complaints are logged in our CRM system. Records are retained for "
                "3 years to support trend analysis and regulatory compliance."
            )),
        ]
    },
    "refund": {
        "filename": "refund_policy.pdf",
        "title": "Refund and Returns Policy",
        "sections": [
            ("Overview", (
                "We want you to be completely satisfied with your purchase. "
                "This policy explains how to return items and obtain a refund."
            )),
            ("Return Window", (
                "You may return most items within 30 days of the delivery date "
                "for a full refund. Items must be unused, in their original packaging, "
                "and accompanied by proof of purchase."
            )),
            ("Non-Returnable Items", (
                "The following items cannot be returned: perishable goods, "
                "digital downloads once accessed, personalised or custom-made items, "
                "hazardous materials, and items marked 'Final Sale'."
            )),
            ("Faulty or Incorrect Items", (
                "If you receive a faulty, damaged, or incorrect item, you may return it "
                "at any time within the statutory warranty period (12 months) for a full "
                "refund, replacement, or repair at your discretion."
            )),
            ("How to Initiate a Return", (
                "Step 1: Contact our support team via chat, email, or phone. "
                "Step 2: Provide your order number and reason for return. "
                "Step 3: You will receive a prepaid return shipping label by email. "
                "Step 4: Pack the item securely and drop it at any approved courier point. "
                "Step 5: Track your return using the label reference."
            )),
            ("Refund Processing", (
                "Once we receive and inspect the returned item, your refund will be "
                "processed within 3-5 business days. The funds will be returned to your "
                "original payment method. You will receive a confirmation email. "
                "Card refunds may take an additional 5-10 business days to appear."
            )),
            ("Partial Refunds", (
                "Partial refunds may be issued for items that are returned in a condition "
                "other than original, missing accessories, or after the standard return window "
                "at the discretion of the returns team."
            )),
            ("Exchange Policy", (
                "Exchanges are processed as a return followed by a new order. "
                "If the replacement item is of higher value, you will be charged the difference. "
                "If lower, the difference will be refunded."
            )),
            ("Return Shipping Costs", (
                "We provide a free prepaid return label for faulty or incorrectly sent items. "
                "For change-of-mind returns, a flat return shipping fee of £3.99 will be "
                "deducted from the refund."
            )),
        ]
    },
    "product_info": {
        "filename": "product_info_policy.pdf",
        "title": "Product Information & Warranty Guide",
        "sections": [
            ("Warranty Coverage", (
                "All products sold by us carry a minimum 12-month manufacturer's warranty "
                "from the date of purchase. Premium and Pro range products carry a 24-month warranty. "
                "The warranty covers defects in materials and workmanship under normal use."
            )),
            ("What the Warranty Does Not Cover", (
                "The warranty does not cover damage caused by: accidental damage, misuse, "
                "unauthorised modifications, normal wear and tear, liquid damage, "
                "or damage caused by use outside the product's intended purpose."
            )),
            ("Extended Warranty", (
                "Customers may purchase an extended warranty at the point of sale or within "
                "30 days of purchase. Extended warranties add 1 or 2 additional years of coverage "
                "and include accidental damage protection."
            )),
            ("Voltage & International Use", (
                "Most of our electronic products support dual voltage (100-240V, 50/60Hz) "
                "and can be used internationally with the appropriate plug adapter. "
                "Check the product label or specifications sheet for voltage details. "
                "Single-voltage products must not be used outside their rated voltage range."
            )),
            ("Compatible Accessories", (
                "We recommend using only manufacturer-approved accessories with our products. "
                "Using third-party accessories may void the warranty. "
                "A full list of compatible accessories is available on each product page."
            )),
            ("Product Specifications", (
                "Detailed specifications for all products, including dimensions, weight, "
                "materials, and technical data, are available on the product listing page "
                "and in the included product manual."
            )),
            ("Software & Firmware Updates", (
                "Smart and connected products receive free firmware updates for a minimum "
                "of 3 years from the launch date. Updates are delivered automatically "
                "when the device is connected to Wi-Fi."
            )),
            ("Safety Certifications", (
                "All electrical products comply with relevant safety standards including "
                "CE, UKCA, and RoHS directives. Certification documents are available on request."
            )),
        ]
    },
    "escalate": {
        "filename": "escalation_policy.pdf",
        "title": "Escalation & Senior Review Policy",
        "sections": [
            ("Purpose", (
                "This policy governs the escalation of customer complaints and service "
                "issues to senior management, ensuring timely and appropriate resolution "
                "for complex or sensitive cases."
            )),
            ("When to Escalate", (
                "A case should be escalated when: the customer is unsatisfied after two "
                "resolution attempts, the issue involves potential legal or regulatory "
                "implications, the complaint involves a senior member of staff, "
                "the financial value exceeds £500, or the customer explicitly requests escalation."
            )),
            ("Escalation Tiers", (
                "Tier 1: Customer Service Representative (standard cases). "
                "Tier 2: Senior Customer Service Manager (complex or repeated complaints). "
                "Tier 3: Head of Customer Experience (unresolved Tier 2 cases, legal threats). "
                "Tier 4: Director level (regulatory complaints, media involvement)."
            )),
            ("Response Timeframes", (
                "Tier 2 escalation: acknowledgement within 4 hours, resolution within 5 business days. "
                "Tier 3 escalation: acknowledgement within 2 hours, resolution within 3 business days. "
                "Tier 4 escalation: immediate acknowledgement, resolution timeline agreed with customer."
            )),
            ("Customer Communication During Escalation", (
                "The customer must be informed when their case is escalated. "
                "They will be given the name and direct contact of their assigned manager. "
                "Progress updates must be provided at least every 2 business days."
            )),
            ("Compensation at Escalation", (
                "Escalated cases are reviewed for goodwill compensation by the Senior Manager. "
                "Compensation may include refunds, account credits, complimentary products, "
                "or a formal written apology signed by a senior representative."
            )),
            ("Final Response Letter", (
                "All escalated cases receive a Final Response Letter within 8 weeks. "
                "This letter outlines the investigation findings, the decision, and any "
                "remedy offered. It also informs the customer of their right to contact "
                "the relevant ombudsman if they remain dissatisfied."
            )),
        ]
    },
    "general": {
        "filename": "general_policy.pdf",
        "title": "General Customer Service Policy",
        "sections": [
            ("Support Hours", (
                "Our AI-powered customer support assistant is available 24 hours a day, "
                "7 days a week, including weekends and public holidays. "
                "For queries requiring a human agent, our team is available: "
                "Monday to Friday: 09:00 - 19:00 (IST). "
                "Saturday: 09:00 - 14:00 (IST). "
                "Sunday and Indian Public Holidays: AI support only."
            )),
            ("Contact Channels", (
                "You can reach us via: Live chat at support.example.com, "
                "Email: support@example.com (response within 1 business day), "
                "Phone: 0800 123 4567 (freephone, UK only), "
                "Post: Customer Services, Example Ltd, 1 Business Park, London, EC1A 1BB."
            )),
            ("Response Time Commitments", (
                "Live chat: Immediate connection during support hours. "
                "Email: Response within 1 business day. "
                "Phone: Average wait time under 3 minutes. "
                "Social media: Monitored Monday-Friday, response within 4 hours."
            )),
            ("Order Tracking", (
                "You can track your order at any time by logging into your account "
                "and visiting 'My Orders', or by using the tracking link in your "
                "dispatch confirmation email. For orders placed as a guest, use the "
                "order number and email address at our tracking page."
            )),
            ("Account Management", (
                "Customers can update their personal details, manage payment methods, "
                "view order history, and manage communication preferences in the "
                "'My Account' section of our website or mobile app."
            )),
            ("Privacy & Data", (
                "We process personal data in accordance with UK GDPR and our Privacy Policy. "
                "You have the right to access, rectify, or erase your personal data at any time "
                "by submitting a request to privacy@example.com."
            )),
            ("Accessibility", (
                "We are committed to making our services accessible to all customers. "
                "Large print correspondence, relay services for hearing-impaired customers, "
                "and extended resolution timeframes for vulnerable customers are available on request."
            )),
            ("Feedback", (
                "We welcome all feedback to help us improve. After each interaction, "
                "you may receive a short satisfaction survey. You can also leave feedback "
                "at any time at feedback.example.com."
            )),
        ]
    },
}


class PolicyPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 8, "CONFIDENTIAL - INTERNAL POLICY DOCUMENT", align="C")
        self.ln(4)
        self.set_draw_color(200, 200, 200)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")


def build_pdf(policy: dict, out_path: Path):
    pdf = PolicyPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # Title
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(15, 23, 42)
    pdf.ln(4)
    pdf.multi_cell(0, 10, policy["title"])
    pdf.ln(2)

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(0, 6, f"Version 2.1  |  Last reviewed: January 2025  |  Owner: Customer Experience")
    pdf.ln(8)

    pdf.set_draw_color(37, 99, 235)
    pdf.set_line_width(0.6)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(8)

    for i, (heading, body) in enumerate(policy["sections"], 1):
        # Section heading
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(0, 7, f"{i}. {heading}")
        pdf.ln(1)

        # Body
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(51, 65, 85)
        pdf.multi_cell(0, 6, body)
        pdf.ln(5)

    pdf.output(str(out_path))
    print(f"  Created: {out_path}")


if __name__ == "__main__":
    print("Generating sample policy PDFs...\n")
    for intent, policy in POLICIES.items():
        dest = OUT_DIR / intent
        dest.mkdir(parents=True, exist_ok=True)
        build_pdf(policy, dest / policy["filename"])
    print(f"\nDone. PDFs written to {OUT_DIR}/")
