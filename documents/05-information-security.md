# Information Security Policy

**Document ID:** POL-005  
**Effective Date:** January 1, 2025  
**Last Revised:** February 1, 2025  
**Department:** Information Technology  

## 1. Purpose

This policy establishes the information security framework for Acme Corporation. It defines the requirements for protecting company data, systems, and networks from unauthorized access, disclosure, modification, or destruction.

## 2. Scope

This policy applies to all employees, contractors, consultants, temporary workers, and third-party users who access Acme Corporation's information systems or data.

## 3. Data Classification

All company data must be classified into one of the following categories:

### 3.1 Public

Information that is freely available to the public. Examples: marketing materials, press releases, public website content.

### 3.2 Internal

Information intended for use within the company. Examples: internal memos, org charts, internal presentations.

### 3.3 Confidential

Sensitive business information that could harm the company if disclosed. Examples: financial reports, strategic plans, customer lists, source code.

### 3.4 Restricted

Highly sensitive information requiring the highest level of protection. Examples: personally identifiable information (PII), payment card data, trade secrets, health records, employee SSNs.

## 4. Access Control

### 4.1 Principle of Least Privilege

Access to information systems and data must be limited to the minimum necessary for employees to perform their job functions. Access rights are reviewed quarterly.

### 4.2 Authentication Requirements

- All systems require multi-factor authentication (MFA).
- Passwords must meet the following requirements:
  - Minimum 14 characters
  - Must include uppercase, lowercase, numbers, and special characters
  - Must not reuse any of the last 12 passwords
  - Must be changed every 90 days
- Biometric authentication is available and encouraged for supported devices.

### 4.3 Account Management

- New accounts are provisioned through the IT Service Desk with manager approval.
- Accounts are deactivated within 4 hours of employee separation.
- Dormant accounts (no login for 60 days) are automatically disabled.
- Service accounts require annual review and re-approval.

## 5. Device Security

### 5.1 Company-Owned Devices

- Full-disk encryption must be enabled (BitLocker for Windows, FileVault for Mac).
- Automatic screen lock after 5 minutes of inactivity.
- Antivirus/EDR software must be installed and kept current.
- Operating system and application patches must be applied within 7 days of release (critical patches within 48 hours).

### 5.2 Personal Devices (BYOD)

- Personal devices used for work must be enrolled in the company MDM (Mobile Device Management) solution.
- A separate work profile/container is required.
- The company reserves the right to remotely wipe the work container.
- Jailbroken or rooted devices are prohibited from accessing company resources.

## 6. Network Security

### 6.1 VPN

- All remote access to company resources must use the approved VPN solution (GlobalProtect).
- Split tunneling is disabled by default.
- VPN sessions automatically disconnect after 12 hours of continuous use.

### 6.2 Wi-Fi

- Company office Wi-Fi uses WPA3 enterprise authentication.
- Guest Wi-Fi is isolated from the corporate network.
- Employees must not connect to public Wi-Fi without using VPN.

### 6.3 Firewall and Monitoring

- All network traffic is monitored by the Security Operations Center (SOC).
- Intrusion detection/prevention systems (IDS/IPS) are deployed at all network boundaries.
- Web filtering blocks access to known malicious sites and inappropriate content.

## 7. Email Security

- Phishing awareness training is mandatory for all employees (quarterly).
- Suspicious emails must be reported to security@acmecorp.com or via the "Report Phishing" button in Outlook.
- External emails are tagged with [EXTERNAL] in the subject line.
- Attachments from unknown senders are sandboxed automatically.
- Email data loss prevention (DLP) rules prevent sending of PII and financial data to external recipients.

## 8. Incident Response

### 8.1 Reporting

All security incidents must be reported immediately to:
- Email: security@acmecorp.com
- Phone: ext. 9111 (24/7 Security Hotline)
- Slack: #security-incidents channel

### 8.2 Incident Classification

| Severity  | Description                                       | Response Time |
|-----------|--------------------------------------------------|---------------|
| Critical  | Active breach, ransomware, data exfiltration     | 15 minutes    |
| High      | Suspected breach, malware detection              | 1 hour        |
| Medium    | Policy violation, suspicious activity            | 4 hours       |
| Low       | Informational, minor policy deviation            | 24 hours      |

### 8.3 Investigation

The Security team will investigate all reported incidents and:
- Contain the threat
- Preserve evidence
- Determine root cause
- Implement remediation
- Report findings to management and affected parties

## 9. Data Protection and Privacy

### 9.1 Data Handling

- Restricted and Confidential data must be encrypted in transit and at rest.
- Data must not be stored on personal devices or unauthorized cloud services.
- Approved cloud storage: Google Workspace, OneDrive for Business.
- USB drives are disabled by default; exceptions require Security team approval.

### 9.2 Data Retention

Data must be retained according to the Data Retention Schedule. When data reaches its retention limit, it must be securely destroyed using approved methods (digital shredding for electronic data, cross-cut shredding for physical documents).

## 10. Compliance and Training

- All employees must complete annual Security Awareness Training.
- Phishing simulation exercises are conducted quarterly.
- Non-compliance may result in disciplinary action, up to and including termination.
- Violations involving data breaches may be reported to regulatory authorities as required by law.

---

*For questions about this policy, contact the Security team at security@acmecorp.com or ext. 9100.*
