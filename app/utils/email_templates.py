# Email templates for Listinker

# Email verification template
EMAIL_VERIFICATION_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8">
    <title>Email Verification - Listinker</title>
  </head>
  <body style="margin:0; padding:0; background:#ffffff; font-family:Segoe UI, Tahoma, Geneva, Verdana, sans-serif; color:#111827;">
    
    <!-- Full width wrapper -->
    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#ffffff; padding:20px 0;">
      <tr>
        <td align="center">
          
          <!-- Card container -->
          <table width="600" cellpadding="0" cellspacing="0" border="0" 
                 style="background:#ffffff; border-radius:8px; box-shadow:0 4px 16px rgba(0,0,0,0.1); padding:30px 40px;">
            <tr>
              <td>
                <!-- Header -->
                <table width="100%" style="margin-bottom:25px;">
                  <tr>
                    <td align="left" style="font-size:28px; font-weight:800; color:#0ea5e9;">
                      Listinker
                    </td>
                    <td align="right">
                      <a href="https://listinker.com" 
                         style="display:inline-block; padding:8px 16px; font-size:14px; font-weight:600; color:#111827; text-decoration:none; border:1px solid #d1d5db; border-radius:6px;">
                        Go to Listinker
                      </a>
                    </td>
                  </tr>
                </table>

                <!-- Content -->
                <h2 style="font-size:22px; font-weight:600; margin:0 0 10px; color:#111827;">
                  Email Verification
                </h2>
                <p style="font-size:15px; line-height:1.6; margin:8px 0; color:#374151;">
                  Please enter this confirmation code in the Listinker Dashboard to verify your email address:
                </p>

                <!-- OTP -->
                <div style="background:#1a1a1b; font-size:42px; font-weight:bold; text-align:center; padding:20px 0; border-radius:6px; margin:25px 0; letter-spacing:6px; color:#0ea5e9;">
                  {{otp_code}}
                </div>

                <!-- Note -->
                <p style="font-size:14px; color:#555; margin-top:15px;">
                  You are receiving this email because you recently added or updated your email address on your Listinker profile. If you did not make this request, you can safely ignore this message.<br>
                  <strong style="color:#111827;">This code will expire in 10 minutes.</strong>
                </p>
              </td>
            </tr>
          </table>
          <!-- End card -->

          <!-- Footer -->
          <div style="text-align:center; font-size:12px; color:#6b7280; margin-top:20px;">
            © {{CURRENT_YEAR}} Listinker. All rights reserved.
          </div>
          
        </td>
      </tr>
    </table>

  </body>
</html>
'''