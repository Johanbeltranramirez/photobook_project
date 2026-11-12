import smtplib
import ssl
from django.core.mail.backends.smtp import EmailBackend as SmtpBackend
from django.core.mail.utils import DNS_NAME


class EmailBackend(SmtpBackend):
    def contexto_ssl(self):
        return ssl.create_default_context()

    def open(self):
        if self.connection:
            return False
        parametros = {'local_hostname': DNS_NAME.get_fqdn()}
        if self.timeout is not None:
            parametros['timeout'] = self.timeout
        contexto = self.contexto_ssl()
        try:
            if self.use_ssl:
                self.connection = smtplib.SMTP_SSL(self.host, self.port, context=contexto, **parametros)
            else:
                self.connection = smtplib.SMTP(self.host, self.port, **parametros)
                if self.use_tls:
                    self.connection.ehlo()
                    self.connection.starttls(context=contexto)
                    self.connection.ehlo()
            if self.username and self.password:
                self.connection.login(self.username, self.password)
            return True
        except OSError:
            if not self.fail_silently:
                raise
