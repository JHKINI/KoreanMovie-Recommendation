import { Component } from 'react'

// 화면을 그리는 중 예외가 나도 흰 화면 대신 안내와 복귀 버튼을 보여준다.
// 주소가 바뀌면(App에서 key를 바꿔) 새로 만들어져 오류 상태가 풀린다.
class ErrorBoundary extends Component {
  state = { error: null }

  static getDerivedStateFromError(error) {
    return { error }
  }

  componentDidCatch(error, info) {
    console.error('화면 오류:', error, info.componentStack)
  }

  render() {
    if (!this.state.error) return this.props.children

    return (
      <div className="page error-page" role="alert">
        <h1 className="page-title">문제가 발생했습니다</h1>
        <p className="section-note">화면을 그리는 중 오류가 났습니다. 처음으로 돌아가 다시 시도해 보세요.</p>
        <a className="primary" href="#/" onClick={() => this.setState({ error: null })}>
          처음으로 돌아가기
        </a>
      </div>
    )
  }
}

export default ErrorBoundary
