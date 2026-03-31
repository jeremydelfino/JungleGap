"""
services/email_service.py
Envoi d'emails via Resend avec template HTML JungleGap.
"""
import os
import resend

resend.api_key = os.getenv("RESEND_API_KEY")

FROM_EMAIL = "noreply@junglegap.fr"

def _html_template(code: str, username: str) -> str:
    digits = list(code)
    digit_cells = "".join([
        f"""
        <td style="
            width: 48px;
            height: 60px;
            background: #1c1c1c;
            border: 1px solid #ffffff12;
            border-radius: 10px;
            text-align: center;
            vertical-align: middle;
            font-family: 'Helvetica Neue', Arial, sans-serif;
            font-size: 28px;
            font-weight: 800;
            color: #e8eaf0;
            padding: 0;
        ">{d}</td>
        <td style="width: 8px;"></td>
        """ for d in digits
    ])

    return f"""
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Vérifie ton email — JungleGap</title>
</head>
<body style="margin:0;padding:0;background:#111111;font-family:'Helvetica Neue',Arial,sans-serif;">

  <!-- Wrapper -->
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#111111;padding:40px 20px;">
    <tr>
      <td align="center">
        <table width="520" cellpadding="0" cellspacing="0" style="
            background:#1a1a1a;
            border:1px solid #ffffff0a;
            border-radius:20px;
            overflow:hidden;
            max-width:520px;
            width:100%;
        ">

          <!-- Header avec glow -->
          <tr>
            <td style="
                background: linear-gradient(135deg, #65BD6215 0%, #1a1a1a 60%);
                padding: 36px 40px 28px;
                border-bottom: 1px solid #ffffff08;
                text-align: center;
            ">
              <!-- Logo -->
              <div style="
                  font-size: 22px;
                  font-weight: 900;
                  letter-spacing: 4px;
                  text-transform: uppercase;
                  background: linear-gradient(90deg, #65BD62, #e2b147);
                  -webkit-background-clip: text;
                  -webkit-text-fill-color: transparent;
                  background-clip: text;
                  display: inline-block;
                  margin-bottom: 4px;
              ">JUNGLEGAP</div>
              <div style="
                  width: 40px;
                  height: 2px;
                  background: linear-gradient(90deg, #65BD62, #e2b147);
                  margin: 8px auto 0;
                  border-radius: 999px;
              "></div>
            </td>
          </tr>

          <!-- Body -->
          <tr>
            <td style="padding: 36px 40px;">

              <!-- Salut -->
              <p style="
                  margin: 0 0 8px;
                  font-size: 22px;
                  font-weight: 700;
                  color: #e8eaf0;
                  line-height: 1.3;
              ">Salut {username} 👋</p>

              <p style="
                  margin: 0 0 32px;
                  font-size: 14px;
                  color: #6b7280;
                  line-height: 1.6;
              ">
                Tu as demandé à créer un compte JungleGap.<br/>
                Entre ce code pour confirmer ton adresse email.
              </p>

              <!-- Code -->
              <table cellpadding="0" cellspacing="0" style="margin: 0 auto 32px;">
                <tr>
                  {digit_cells}
                </tr>
              </table>

              <!-- Expiration -->
              <table width="100%" cellpadding="0" cellspacing="0" style="
                  background: #e2b14710;
                  border: 1px solid #e2b14725;
                  border-radius: 10px;
                  margin-bottom: 32px;
              ">
                <tr>
                  <td style="padding: 12px 16px;">
                    <p style="margin:0;font-size:13px;color:#e2b147;font-weight:500;">
                      ⏱ Ce code expire dans <strong>10 minutes</strong>
                    </p>
                  </td>
                </tr>
              </table>

              <!-- Séparateur -->
              <div style="height:1px;background:#ffffff08;margin-bottom:28px;"></div>

              <!-- Info sécurité -->
              <p style="margin:0;font-size:12px;color:#4b5563;line-height:1.6;">
                Si tu n'es pas à l'origine de cette demande, ignore simplement cet email.<br/>
                Ton compte ne sera pas créé sans la vérification.
              </p>

            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="
                padding: 20px 40px;
                border-top: 1px solid #ffffff08;
                text-align: center;
            ">
              <p style="margin:0;font-size:11px;color:#374151;">
                © 2025 JungleGap · Paris virtuels League of Legends
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>

</body>
</html>
"""


def send_verification_code(email: str, code: str, username: str = "invocateur") -> bool:
    """
    Envoie le code de vérification par email via Resend.
    Retourne True si succès, False sinon.
    """
    try:
        resend.Emails.send({
            "from":    FROM_EMAIL,
            "to":      [email],
            "subject": f"{code} est ton code JungleGap",
            "html":    _html_template(code, username),
        })
        print(f"[email] Code envoyé à {email}")
        return True
    except Exception as e:
        print(f"[email] Erreur Resend : {e}")
        # Fallback console
        print(f"\n{'='*44}")
        print(f"  📧  CODE DE VÉRIFICATION (fallback console)")
        print(f"  Destinataire : {email}")
        print(f"  Code         : {code}")
        print(f"{'='*44}\n")
        return False