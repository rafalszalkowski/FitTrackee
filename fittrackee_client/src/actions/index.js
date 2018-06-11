import FitTrackeeApi from '../fitTrackeeApi/index'
import { history } from '../index'


export const setData = (target, data) => ({
  type: 'SET_DATA',
  data,
  target,
})

export const setError = message => ({
  type: 'SET_ERROR',
  message,
})

export const setLoading = loading => ({
  type: 'SET_LOADING',
  loading
})

export const getData = (target, data) => dispatch => {
  if (data && data.id && isNaN(data.id)) {
    return dispatch(setError(target, `${target}: Incorrect id`))
  }
  return FitTrackeeApi
  .getData(target, data)
  .then(ret => {
    if (ret.status === 'success') {
      dispatch(setData(target, ret.data))
    } else {
      dispatch(setError(`${target}: ${ret.message}`))
    }
  })
  .catch(error => dispatch(setError(`${target}: ${error}`)))
}

export const addData = (target, data) => dispatch => FitTrackeeApi
  .addData(target, data)
  .then(ret => {
    if (ret.status === 'created') {
      history.push(`/admin/${target}`)
    } else {
      dispatch(setError(`${target}: ${ret.status}`))
    }
  })
  .catch(error => dispatch(setError(`${target}: ${error}`)))

export const updateData = (target, data) => dispatch => {
  if (isNaN(data.id)) {
    return dispatch(setError(target, `${target}: Incorrect id`))
  }
  return FitTrackeeApi
  .updateData(target, data)
  .then(ret => {
    if (ret.status === 'success') {
      dispatch(setData(target, ret.data))
    } else {
      dispatch(setError(`${target}: ${ret.message}`))
    }
  })
  .catch(error => dispatch(setError(`${target}: ${error}`)))
}

export const deleteData = (target, id) => dispatch => {
  if (isNaN(id)) {
    return dispatch(setError(target, `${target}: Incorrect id`))
  }
  return FitTrackeeApi
  .deleteData(target, id)
  .then(ret => {
    if (ret.status === 204) {
      history.push(`/admin/${target}`)
    } else {
      dispatch(setError(`${target}: ${ret.message}`))
    }
  })
  .catch(error => dispatch(setError(`${target}: ${error}`)))
}