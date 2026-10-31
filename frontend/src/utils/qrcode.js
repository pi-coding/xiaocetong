import QRCode from 'qrcode'

export const buildQrDataUrl = (text, size = 240) =>
  QRCode.toDataURL(String(text), {
    width: size,
    margin: 1,
    errorCorrectionLevel: 'M',
    color: { dark: '#0e5a60', light: '#ffffff' },
  })

export const downloadDataUrl = (dataUrl, filename) => {
  const link = document.createElement('a')
  link.href = dataUrl
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}