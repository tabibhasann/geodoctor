# Security Policy

## Supported Versions

We release patches for security vulnerabilities for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 0.2.x   | :white_check_mark: |
| 0.1.x   | :x:                |
| < 0.1   | :x:                |

## Reporting a Vulnerability

We take the security of geodoctor seriously. If you believe you have found a security vulnerability, please report it to us as described below.

**Please do NOT report security vulnerabilities through public GitHub issues.**

### How to Report

Please send an email to [SECURITY_EMAIL] with:

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Any suggested fixes (if you have them)

You should receive a response within 48 hours. If for some reason you do not, please follow up via email to ensure we received your original message.

### What to Expect

1. **Acknowledgment**: We will acknowledge receipt of your vulnerability report within 48 hours
2. **Assessment**: We will investigate and assess the impact and severity
3. **Updates**: We will keep you informed of our progress
4. **Resolution**: We will work to fix the vulnerability and release a patch
5. **Disclosure**: Once fixed, we will publicly disclose the vulnerability (with your permission)

### Disclosure Policy

- We will disclose vulnerabilities after a fix is available
- We will credit reporters unless they request anonymity
- We aim to disclose within 90 days of receiving a report
- Critical vulnerabilities may be disclosed sooner

## Security Best Practices

When using geodoctor:

1. **Input Validation**: Always validate input data before processing
2. **File Permissions**: Use appropriate file permissions for sensitive data
3. **Dependencies**: Keep dependencies up to date
4. **Network Security**: Be cautious when processing data from untrusted sources
5. **Resource Limits**: Set appropriate limits for memory and processing time

## Security Updates

Security updates will be released as patch versions and announced via:

- GitHub Security Advisories
- Release notes
- PyPI notifications

## Dependency Security

We monitor our dependencies for security vulnerabilities:

- Dependabot is configured for automated updates
- We regularly review and update dependencies
- Critical dependency vulnerabilities are prioritized

## Contact

For security-related questions or concerns:

- Email: [SECURITY_EMAIL]
- Security Advisory: [GitHub Security Advisories URL]

## Security Hall of Fame

We appreciate responsible disclosure and will acknowledge contributors who report security vulnerabilities (unless they prefer to remain anonymous).

Thank you for helping keep geodoctor and its users safe! 🔒
