from django import forms


class SendMessageForm(forms.Form):
    send_type = forms.ChoiceField(label='Send Type', choices=(('smpp', 'SMPP'), ('http', 'HTTP')), initial='smpp')
    src_addr = forms.CharField(label='Header', max_length=20, initial="JasminSMS")
    dst_addr = forms.CharField(label='MSISDN', max_length=20, initial='')
    text = forms.CharField(label='Message', max_length=500, initial='test message', widget=forms.Textarea())
