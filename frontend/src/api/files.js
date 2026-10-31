import request from './request'

export const uploadImage = (file) => {
  const form = new FormData()
  form.append('file', file)
  return request.post('/files/upload', form)
}