import ipaddress
import ssl
from functools import partial
from pathlib import Path
from datetime import datetime, timedelta

from django.core.management.commands.runserver import Command as RunserverCommand
from django.core.servers.basehttp import WSGIServer

try:
    from OpenSSL import crypto
except ImportError:  # pragma: no cover
    crypto = None


class SSLWSGIServer(WSGIServer):
    def __init__(self, *args, ssl_context=None, **kwargs):
        self.ssl_context = ssl_context
        super().__init__(*args, **kwargs)

    def server_bind(self):
        super().server_bind()
        if self.ssl_context is not None:
            self.socket = self.ssl_context.wrap_socket(self.socket, server_side=True)


class Command(RunserverCommand):
    help = (
        'Starts Django development server using HTTPS. '
        'Generates a self-signed certificate if none exists.'
    )

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            '--certfile',
            default='cert.pem',
            help='Path to SSL certificate file.',
        )
        parser.add_argument(
            '--keyfile',
            default='key.pem',
            help='Path to SSL private key file.',
        )
        parser.add_argument(
            '--generate-cert',
            action='store_true',
            dest='generate_cert',
            help='Generate a self-signed certificate and key if missing.',
        )
        parser.add_argument(
            '--cert-host',
            action='append',
            dest='cert_hosts',
            default=[],
            help='Add a hostname or IP address to the certificate SAN. May be repeated.',
        )

    def inner_run(self, *args, **options):
        certfile = Path(options['certfile'])
        keyfile = Path(options['keyfile'])

        cert_hosts = []
        for host_value in options.get('cert_hosts', []):
            for token in str(host_value).split(','):
                token = token.strip()
                if token:
                    cert_hosts.append(token)

        if options['generate_cert'] or not (certfile.exists() and keyfile.exists()):
            self.generate_self_signed_cert(certfile, keyfile, cert_hosts)

        ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_context.load_cert_chain(certfile=str(certfile), keyfile=str(keyfile))

        self.server_cls = partial(SSLWSGIServer, ssl_context=ssl_context)
        return super().inner_run(*args, **options)

    def generate_self_signed_cert(self, certfile: Path, keyfile: Path, cert_hosts=None):
        if certfile.exists() and keyfile.exists() and not cert_hosts:
            return

        if certfile.exists() and keyfile.exists() and cert_hosts:
            certfile.unlink()
            keyfile.unlink()

        cert_hosts = cert_hosts or []
        if not cert_hosts:
            cert_hosts = ['localhost', '127.0.0.1']

        if crypto is None:
            raise RuntimeError(
                'pyOpenSSL is required to generate a self-signed certificate. '
                'Install it with `pip install pyOpenSSL`.'
            )

        key = crypto.PKey()
        key.generate_key(crypto.TYPE_RSA, 2048)

        cert = crypto.X509()
        cert.get_subject().CN = cert_hosts[0]
        cert.set_serial_number(int(datetime.utcnow().timestamp()))
        cert.gmtime_adj_notBefore(0)
        cert.gmtime_adj_notAfter(365 * 24 * 60 * 60)
        cert.set_issuer(cert.get_subject())
        cert.set_pubkey(key)

        sans = []
        for host in cert_hosts:
            try:
                ipaddress.ip_address(host)
                sans.append(f'IP:{host}')
            except ValueError:
                sans.append(f'DNS:{host}')

        cert.add_extensions([
            crypto.X509Extension(
                b'subjectAltName',
                False,
                ', '.join(sans).encode('utf-8')
            )
        ])

        cert.sign(key, 'sha256')

        certfile.write_bytes(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
        keyfile.write_bytes(crypto.dump_privatekey(crypto.FILETYPE_PEM, key))
        if certfile.exists() and keyfile.exists():
            return

        if crypto is None:
            raise RuntimeError(
                'pyOpenSSL is required to generate a self-signed certificate. '
                'Install it with `pip install pyOpenSSL`.'
            )

        key = crypto.PKey()
        key.generate_key(crypto.TYPE_RSA, 2048)

        cert = crypto.X509()
        cert.get_subject().CN = 'localhost'
        cert.set_serial_number(int(datetime.utcnow().timestamp()))
        cert.gmtime_adj_notBefore(0)
        cert.gmtime_adj_notAfter(365 * 24 * 60 * 60)
        cert.set_issuer(cert.get_subject())
        cert.set_pubkey(key)
        cert.sign(key, 'sha256')

        certfile.write_bytes(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
        keyfile.write_bytes(crypto.dump_privatekey(crypto.FILETYPE_PEM, key))
