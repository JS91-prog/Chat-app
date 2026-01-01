from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import datetime
import socket
import ipaddress  # Moved import to top

def get_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def generate_cert():
    local_ip = get_ip_address()
    print(f"Generating certificate for IP: {local_ip} and localhost...")

    # 1. Generate Private Key
    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    # 2. Generate Certificate
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, u"US"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u"Home"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, u"LocalNetwork"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"Secure Chat App"),
        x509.NameAttribute(NameOID.COMMON_NAME, u"localhost"),
    ])

    # --- FIXED SECTION START ---
    # Create the list of alternative names
    alt_names_list = [x509.DNSName(u"localhost")]
    
    # Add IPs safely
    for ip in ["127.0.0.1", local_ip]:
        try:
            alt_names_list.append(x509.IPAddress(ipaddress.ip_address(ip)))
        except ValueError:
            pass # Skip invalid IPs
            
    # --- FIXED SECTION END ---

    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.now(datetime.timezone.utc)
    ).not_valid_after(
        datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=365)
    ).add_extension(
        x509.SubjectAlternativeName(alt_names_list),
        critical=False,
    ).sign(key, hashes.SHA256())

    # 3. Save Files
    with open("key.pem", "wb") as f:
        f.write(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ))

    with open("cert.pem", "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    print("✅ certificates generated: cert.pem and key.pem")

if __name__ == "__main__":
    generate_cert()
