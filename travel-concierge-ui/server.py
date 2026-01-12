#!/usr/bin/env python3
"""
Travel Concierge Chat UI Backend Server
Agent Engine API 프록시 및 로그 조회 서버
"""

import os
import sys
import json
import asyncio
import threading
import queue
import time
from datetime import datetime, timedelta
from typing import Optional, Dict

from flask import Flask, request, jsonify, Response, stream_with_context, send_from_directory
from flask_cors import CORS
import google.auth
from google.auth.transport.requests import Request
from google.cloud import logging_v2
from google.cloud import pubsub_v1
from google.api_core import exceptions
import vertexai
from vertexai import agent_engines
from google.adk.sessions import VertexAiSessionService

# 현재 디렉토리를 기준으로 정적 파일 서빙
app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)  # CORS 활성화

# 환경 변수
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "gsneotek-ncc-demo")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

# Vertex AI 초기화
vertexai.init(project=PROJECT_ID, location=LOCATION)

# 세션 서비스
session_service = VertexAiSessionService(PROJECT_ID, LOCATION)

# 로그 클라이언트
logging_client = logging_v2.Client(project=PROJECT_ID)

# Pub/Sub 클라이언트
publisher = pubsub_v1.PublisherClient()
subscriber = pubsub_v1.SubscriberClient()

# Pub/Sub Topic 이름
TOPIC_NAME = "agent-engine-responses"
TOPIC_PATH = publisher.topic_path(PROJECT_ID, TOPIC_NAME)

# 세션별 메시지 큐 (Pub/Sub 구독 전용)
session_queues: Dict[str, queue.Queue] = {}
session_subscriptions: Dict[str, pubsub_v1.subscriber.futures.StreamingPullFuture] = {}

# Topic 생성 (없으면 생성)
def ensure_topic_exists():
    """Topic이 존재하는지 확인하고 없으면 생성"""
    try:
        topic = publisher.get_topic(request={"topic": TOPIC_PATH})
        print(f"Topic {TOPIC_NAME} already exists")
    except exceptions.NotFound:
        try:
            topic = publisher.create_topic(request={"name": TOPIC_PATH})
            print(f"Created topic {TOPIC_NAME}")
        except Exception as e:
            print(f"Error creating topic: {e}")
            # Topic 생성 실패해도 계속 진행 (이미 존재할 수 있음)

# 앱 시작 시 Topic 확인
ensure_topic_exists()


@app.route("/")
def index():
    """메인 페이지"""
    return send_from_directory('.', 'index.html')


@app.route("/<path:filename>")
def serve_static(filename):
    """정적 파일 서빙 (CSS, JS 등)"""
    # API 경로는 제외
    if filename.startswith('api/'):
        return jsonify({"error": "Not found"}), 404
    return send_from_directory('.', filename)


@app.route("/api/health", methods=["GET"])
def health():
    """헬스 체크"""
    return jsonify({"status": "ok", "project": PROJECT_ID, "location": LOCATION})


@app.route("/api/session", methods=["POST"])
def create_session():
    """새 세션 생성"""
    try:
        data = request.json
        project_id = data.get("projectId", PROJECT_ID)
        location = data.get("location", LOCATION)
        resource_id = data.get("resourceId")
        user_id = data.get("userId", f"user-{datetime.now().timestamp()}")
        
        if not resource_id:
            return jsonify({"error": "resourceId is required"}), 400
        
        # Resource name 생성
        if resource_id.isdigit():
            resource_name = f"projects/{project_id}/locations/{location}/reasoningEngines/{resource_id}"
        else:
            resource_name = resource_id
        
        # 세션 생성 (async 함수를 동기적으로 실행)
        session = asyncio.run(session_service.create_session(
            app_name=resource_name,
            user_id=user_id,
        ))
        
        return jsonify({
            "sessionId": session.id,
            "userId": user_id,
            "resourceName": resource_name,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def event_to_dict(event):
    """이벤트 객체를 dict로 변환"""
    if isinstance(event, dict):
        return event
    
    event_dict = {}
    if hasattr(event, '__dict__'):
        event_dict = event.__dict__.copy()
    elif hasattr(event, '__iter__') and not isinstance(event, (str, bytes)):
        try:
            event_dict = dict(event)
        except:
            event_dict = {"str": str(event)}
    else:
        event_dict = {"str": str(event)}
    
    # 재귀적으로 객체 속성도 변환
    for key, value in event_dict.items():
        if hasattr(value, '__dict__'):
            event_dict[key] = event_to_dict(value)
    
    return event_dict


def extract_content_from_event(event):
    """이벤트에서 콘텐츠 추출"""
    is_dict = isinstance(event, dict)
    
    # Content 가져오기
    content = None
    if is_dict:
        content = event.get("content")
    else:
        content = getattr(event, 'content', None)
    
    if content is None:
        # 디버깅: 이벤트 구조 확인
        print(f"DEBUG: extract_content_from_event - content is None. Event type: {type(event)}, Event keys: {list(event.keys()) if is_dict else 'N/A'}")
        return None
    
    # Parts 가져오기
    parts = None
    if isinstance(content, dict):
        parts = content.get("parts", [])
    elif hasattr(content, 'parts'):
        parts = content.parts
    else:
        return None
    
    if not parts:
        return None
    
    results = {
        "text": None,
        "thought": False,
        "function_call": None,
        "function_response": None,
    }
    
    text_parts = []  # 여러 텍스트 part를 누적
    
    for part in parts:
        is_part_dict = isinstance(part, dict)
        
        # 텍스트 콘텐츠
        text = None
        thought = False
        if is_part_dict:
            text = part.get("text")
            thought = part.get("thought", False)
        else:
            text = getattr(part, 'text', None)
            thought = getattr(part, 'thought', False)
        
        if text and not thought:
            text_parts.append(text)
        
        # Function call
        func_call = None
        if is_part_dict:
            func_call = part.get("functionCall") or part.get("function_call")
        else:
            func_call = getattr(part, 'function_call', None)
        
        if func_call:
            if isinstance(func_call, dict):
                results["function_call"] = {
                    "name": func_call.get("name", "unknown"),
                    "args": func_call.get("args", {}),
                }
            else:
                results["function_call"] = {
                    "name": getattr(func_call, 'name', 'unknown'),
                    "args": getattr(func_call, 'args', {}),
                }
        
        # Function response
        func_response = None
        if is_part_dict:
            func_response = part.get("functionResponse") or part.get("function_response")
        else:
            func_response = getattr(part, 'function_response', None)
        
        if func_response:
            if isinstance(func_response, dict):
                results["function_response"] = {
                    "name": func_response.get("name", "unknown"),
                    "response": func_response.get("response", {}),
                }
            else:
                results["function_response"] = {
                    "name": getattr(func_response, 'name', 'unknown'),
                    "response": getattr(func_response, 'response', {}),
                }
    
    # 모든 텍스트 part를 합침
    if text_parts:
        results["text"] = "".join(text_parts)
    
    return results


def agent_worker(resource_name, user_id, session_id, message, request_id):
    """Agent Engine 응답을 Pub/Sub로 발행하는 워커"""
    try:
        agent_engine = agent_engines.get(resource_name)
        event_count = 0
        content_received = False
        
        for event in agent_engine.stream_query(
            user_id=user_id,
            session_id=session_id,
            message=message,
        ):
            if event is None:
                continue
            
            event_count += 1
            
            # 이벤트를 dict로 변환
            event_dict = event_to_dict(event)
            
            # 콘텐츠 추출
            content_data = extract_content_from_event(event)
            
            # 디버깅: 이벤트 구조 로깅
            if event_count <= 3:  # 처음 3개 이벤트만 로깅
                print(f"DEBUG [Event #{event_count}]: content_data = {content_data}")
                if content_data is None:
                    print(f"DEBUG [Event #{event_count}]: event_dict keys = {list(event_dict.keys()) if isinstance(event_dict, dict) else 'N/A'}")
                    if isinstance(event_dict, dict) and "content" in event_dict:
                        print(f"DEBUG [Event #{event_count}]: event_dict['content'] = {event_dict.get('content')}")
            
            # Pub/Sub 메시지 데이터 구성
            message_data = {
                "type": "agent_event",
                "event_count": event_count,
                "request_id": request_id,
                "event": event_dict,
                "content": content_data,
            }
            
            # Pub/Sub로 발행 (세션 ID를 속성으로 포함)
            # 동기적으로 발행하여 메시지가 확실히 전달되도록 함
            try:
                future = publisher.publish(
                    TOPIC_PATH,
                    json.dumps(message_data, ensure_ascii=False, default=str).encode('utf-8'),
                    session_id=session_id,
                    request_id=request_id,
                )
                # 발행 결과 확인 (타임아웃: 5초)
                future.result(timeout=5.0)
            except Exception as e:
                print(f"ERROR: Pub/Sub 발행 실패 [Event #{event_count}]: {e}")
                # 발행 실패해도 계속 진행
            
            # 콘텐츠가 있으면 플래그 설정 (text가 None이 아니고 빈 문자열이 아닌 경우)
            if content_data:
                text_content = content_data.get("text")
                if text_content is not None and text_content.strip():
                    content_received = True
        
        # 완료 메시지 발행 (모든 이벤트가 발행된 후)
        import time
        time.sleep(0.5)  # 마지막 이벤트가 발행될 시간을 줌
        
        completion_data = {
            "type": "done",
            "request_id": request_id,
            "event_count": event_count,
            "content_received": content_received,
        }
        try:
            future = publisher.publish(
                TOPIC_PATH,
                json.dumps(completion_data, ensure_ascii=False).encode('utf-8'),
                session_id=session_id,
                request_id=request_id,
            )
            future.result(timeout=5.0)
        except Exception as e:
            print(f"ERROR: 완료 메시지 발행 실패: {e}")
        
    except Exception as e:
        import traceback
        error_data = {
            "type": "error",
            "request_id": request_id,
            "message": str(e),
            "traceback": traceback.format_exc(),
        }
        publisher.publish(
            TOPIC_PATH,
            json.dumps(error_data, ensure_ascii=False).encode('utf-8'),
            session_id=session_id,
            request_id=request_id,
        )


@app.route("/api/chat", methods=["POST"])
def chat():
    """Agent Engine에 메시지 전송 및 Pub/Sub 기반 스트리밍 응답"""
    try:
        data = request.json
        project_id = data.get("projectId", PROJECT_ID)
        location = data.get("location", LOCATION)
        resource_id = data.get("resourceId")
        user_id = data.get("userId")
        session_id = data.get("sessionId")
        message = data.get("message")
        
        if not all([resource_id, user_id, session_id, message]):
            return jsonify({"error": "Missing required parameters"}), 400
        
        # Resource name 생성
        if resource_id.isdigit():
            resource_name = f"projects/{project_id}/locations/{location}/reasoningEngines/{resource_id}"
        else:
            resource_name = resource_id
        
        # 요청 ID 생성 (고유 식별자)
        request_id = f"{session_id}-{int(time.time() * 1000)}"
        
        # 세션별 큐 생성
        if session_id not in session_queues:
            session_queues[session_id] = queue.Queue()
        
        # Subscription 이름 생성
        subscription_name = f"agent-response-{session_id.replace('/', '-')}"
        subscription_path = subscriber.subscription_path(PROJECT_ID, subscription_name)
        
        # Subscription 생성 (없으면 생성)
        subscription_created = False
        try:
            subscriber.get_subscription(request={"subscription": subscription_path})
        except exceptions.NotFound:
            try:
                subscriber.create_subscription(
                    request={
                        "name": subscription_path,
                        "topic": TOPIC_PATH,
                        "filter": f'attributes.session_id="{session_id}"',
                    }
                )
                subscription_created = True
                print(f"Created subscription {subscription_name}")
            except Exception as e:
                print(f"Error creating subscription: {e}")
                # Subscription 생성 실패 시 필터 없이 생성 시도
                try:
                    subscriber.create_subscription(
                        request={
                            "name": subscription_path,
                            "topic": TOPIC_PATH,
                        }
                    )
                    subscription_created = True
                except Exception as e2:
                    print(f"Error creating subscription without filter: {e2}")
        
        # Agent Engine 워커 스레드 시작
        worker_thread = threading.Thread(
            target=agent_worker,
            args=(resource_name, user_id, session_id, message, request_id),
            daemon=True
        )
        worker_thread.start()
        
        def generate():
            """SSE 스트리밍 생성기 (Pub/Sub에서 메시지 구독)"""
            try:
                # 디버그: 시작 메시지
                debug_log = {
                    "type": "debug",
                    "message": f"Pub/Sub 기반 스트리밍 시작 (Request ID: {request_id})",
                }
                yield f"data: {json.dumps(debug_log)}\n\n"
                
                # Pub/Sub 구독 콜백
                def callback(message):
                    try:
                        data = json.loads(message.data.decode('utf-8'))
                        # 세션 ID와 요청 ID 확인
                        msg_session_id = message.attributes.get('session_id', '')
                        msg_request_id = data.get('request_id', '')
                        
                        # 디버깅: 받은 메시지 로깅
                        msg_type = data.get('type', 'unknown')
                        if msg_type == 'agent_event':
                            content_data = data.get('content')
                            event_count = data.get('event_count', '?')
                            if content_data and content_data.get('text'):
                                print(f"DEBUG [Pub/Sub 수신] Event #{event_count}: text={content_data.get('text')[:50]}...")
                            else:
                                print(f"DEBUG [Pub/Sub 수신] Event #{event_count}: content_data={content_data}")
                        
                        # 현재 세션과 요청의 메시지만 처리
                        if msg_session_id == session_id and msg_request_id == request_id:
                            session_queues[session_id].put(data)
                            if msg_type == 'agent_event':
                                print(f"DEBUG [Pub/Sub 큐 추가] Event #{data.get('event_count', '?')} 큐에 추가됨")
                        else:
                            print(f"DEBUG [Pub/Sub 필터링] 세션/요청 ID 불일치: msg_session={msg_session_id}, msg_request={msg_request_id}, session={session_id}, request={request_id}")
                        message.ack()
                    except Exception as e:
                        print(f"Error processing Pub/Sub message: {e}")
                        import traceback
                        traceback.print_exc()
                        message.nack()
                
                # 구독 시작
                streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)
                
                try:
                    content_received = False
                    done_received = False
                    timeout_count = 0
                    max_timeout = 300  # 5분 타임아웃
                    
                    while not done_received and timeout_count < max_timeout:
                        try:
                            # 큐에서 메시지 가져오기 (타임아웃: 1초)
                            msg = session_queues[session_id].get(timeout=1.0)
                            timeout_count = 0  # 메시지 받으면 타임아웃 카운터 리셋
                            
                            msg_type = msg.get("type")
                            
                            if msg_type == "agent_event":
                                # 이벤트 처리
                                content_data = msg.get("content")
                                
                                # 디버깅: 메시지 구조 확인
                                if not content_data:
                                    debug_log = {
                                        "type": "debug",
                                        "message": f"⚠️ [Event #{msg.get('event_count', '?')}] content_data가 None입니다. event 구조 확인 필요.",
                                    }
                                    yield f"data: {json.dumps(debug_log, ensure_ascii=False)}\n\n"
                                
                                if content_data:
                                    # 텍스트 콘텐츠 (None이 아니고 빈 문자열이 아닌 경우)
                                    # 모든 이벤트의 텍스트를 확인하고 표시 - 이것이 가장 중요!
                                    text_content = content_data.get("text")
                                    if text_content is not None and text_content.strip():
                                        content_received = True
                                        event_dict = {
                                            "type": "content",
                                            "content": text_content,
                                        }
                                        yield f"data: {json.dumps(event_dict, ensure_ascii=False)}\n\n"
                                    
                                    # Function call
                                    func_call = content_data.get("function_call")
                                    if func_call:
                                        tool_name = func_call.get("name", "unknown")
                                        
                                        event_dict = {
                                            "type": "tool_call",
                                            "tool_name": tool_name,
                                            "args": func_call.get("args", {}),
                                        }
                                        yield f"data: {json.dumps(event_dict, ensure_ascii=False)}\n\n"
                                        
                                        # transfer_to_agent인 경우 사용자에게 알림
                                        if tool_name == "transfer_to_agent":
                                            agent_name = func_call.get("args", {}).get("agent_name", "unknown")
                                            debug_log = {
                                                "type": "debug",
                                                "message": f"🔄 에이전트 전환: {agent_name}",
                                            }
                                            yield f"data: {json.dumps(debug_log, ensure_ascii=False)}\n\n"
                                        else:
                                            debug_log = {
                                                "type": "debug",
                                                "message": f"🔧 Tool 호출: {tool_name}",
                                            }
                                            yield f"data: {json.dumps(debug_log, ensure_ascii=False)}\n\n"
                                    
                                    # Function response
                                    func_response = content_data.get("function_response")
                                    if func_response:
                                        tool_name = func_response.get("name", "unknown")
                                        response = func_response.get("response", {})
                                        
                                        event_dict = {
                                            "type": "tool_response",
                                            "tool_name": tool_name,
                                            "response": response,
                                        }
                                        yield f"data: {json.dumps(event_dict, ensure_ascii=False)}\n\n"
                                        
                                        # Zendesk 티켓 데이터 포맷팅 (기존 로직 유지)
                                        if tool_name in ["zendesk_list_tickets", "zendesk_get_tickets"] and isinstance(response, dict):
                                            payload = response.get("connectorOutputPayload")
                                            
                                            if tool_name == "zendesk_list_tickets" and payload and isinstance(payload, list):
                                                ticket_summary = f"■ 티켓 {len(payload)}개 발견:\n\n"
                                                for idx, ticket in enumerate(payload[:5], 1):
                                                    ticket_id = ticket.get("Id", "N/A")
                                                    if isinstance(ticket_id, float):
                                                        ticket_id = int(ticket_id)
                                                    
                                                    subject = ticket.get("Subject") or ticket.get("RawSubject") or "제목 없음"
                                                    status = ticket.get("Status", "unknown")
                                                    priority = ticket.get("Priority")
                                                    
                                                    ticket_summary += f"{idx}. 티켓 #{ticket_id}: {subject}\n"
                                                    ticket_summary += f"   상태: {status}, 우선순위: {priority or 'None'}\n\n"
                                                
                                                if len(payload) > 5:
                                                    ticket_summary += f"... 외 {len(payload) - 5}개 티켓\n"
                                                
                                                content_received = True
                                                event_dict = {
                                                    "type": "content",
                                                    "content": ticket_summary,
                                                }
                                                yield f"data: {json.dumps(event_dict, ensure_ascii=False)}\n\n"
                                            
                                            elif tool_name == "zendesk_get_tickets" and payload:
                                                ticket = payload if isinstance(payload, dict) else {}
                                                ticket_id = ticket.get("Id", "N/A")
                                                if isinstance(ticket_id, float):
                                                    ticket_id = int(ticket_id)
                                                
                                                subject = ticket.get("Subject") or ticket.get("RawSubject") or ""
                                                description = ticket.get("Description", "")
                                                status = ticket.get("Status", "")
                                                priority = ticket.get("Priority")
                                                requester_id = ticket.get("RequesterId")
                                                created_at = ticket.get("CreatedAt", "")
                                                updated_at = ticket.get("UpdatedAt", "")
                                                
                                                ticket_detail = "\n"
                                                ticket_detail += f"**Id:** {ticket_id}\n"
                                                
                                                if subject:
                                                    ticket_detail += f"**Subject:** {subject}\n"
                                                if description:
                                                    ticket_detail += f"**Description:** {description}\n"
                                                if status:
                                                    ticket_detail += f"**Status:** {status}\n"
                                                if priority is not None:
                                                    ticket_detail += f"**Priority:** {priority}\n"
                                                else:
                                                    ticket_detail += f"**Priority:** null\n"
                                                if requester_id:
                                                    if isinstance(requester_id, float):
                                                        requester_id = int(requester_id)
                                                    ticket_detail += f"**Creator:** {requester_id}\n"
                                                if created_at:
                                                    ticket_detail += f"**Created Time:** {created_at}\n"
                                                if updated_at:
                                                    ticket_detail += f"**Updated Time:** {updated_at}\n"
                                                
                                                content_received = True
                                                event_dict = {
                                                    "type": "content",
                                                    "content": ticket_detail,
                                                }
                                                yield f"data: {json.dumps(event_dict, ensure_ascii=False)}\n\n"
                                        
                                        debug_log = {
                                            "type": "debug",
                                            "message": f"✅ Tool 응답: {tool_name}",
                                        }
                                        yield f"data: {json.dumps(debug_log, ensure_ascii=False)}\n\n"
                            
                            elif msg_type == "done":
                                done_received = True
                                completion_log = {
                                    "type": "debug",
                                    "message": f"Agent Engine 응답 완료 (총 {msg.get('event_count', 0)}개 이벤트, 콘텐츠: {'있음' if content_received else '없음'})",
                                }
                                yield f"data: {json.dumps(completion_log, ensure_ascii=False)}\n\n"
                                yield f"data: {json.dumps({'type': 'done', 'content_received': content_received}, ensure_ascii=False)}\n\n"
                            
                            elif msg_type == "error":
                                error_dict = {
                                    "type": "error",
                                    "message": msg.get("message", "Unknown error"),
                                }
                                yield f"data: {json.dumps(error_dict, ensure_ascii=False)}\n\n"
                                done_received = True
                        
                        except queue.Empty:
                            timeout_count += 1
                            # 하트비트 전송 (연결 유지)
                            if timeout_count % 10 == 0:  # 10초마다
                                yield f"data: {json.dumps({'type': 'heartbeat'}, ensure_ascii=False)}\n\n"
                    
                    # 타임아웃 처리
                    if timeout_count >= max_timeout:
                        error_dict = {
                            "type": "error",
                            "message": "응답 타임아웃 (5분)",
                        }
                        yield f"data: {json.dumps(error_dict, ensure_ascii=False)}\n\n"
                
                finally:
                    # 구독 취소
                    streaming_pull_future.cancel()
                    try:
                        streaming_pull_future.result(timeout=5)
                    except Exception:
                        pass
                    
                    # 큐 정리
                    if session_id in session_queues:
                        # 큐에 남은 메시지 제거
                        while not session_queues[session_id].empty():
                            try:
                                session_queues[session_id].get_nowait()
                            except queue.Empty:
                                break
                
            except Exception as e:
                import traceback
                error_dict = {
                    "type": "error",
                    "message": str(e),
                    "traceback": traceback.format_exc(),
                }
                yield f"data: {json.dumps(error_dict, ensure_ascii=False)}\n\n"
        
        return Response(
            stream_with_context(generate()),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )
        
    except Exception as e:
        import traceback
        return jsonify({
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@app.route("/api/logs", methods=["GET"])
def get_logs():
    """Agent Engine 로그 조회"""
    try:
        project_id = request.args.get("projectId", PROJECT_ID)
        resource_id = request.args.get("resourceId")
        limit = int(request.args.get("limit", 50))
        minutes = int(request.args.get("minutes", 5))  # 조회할 시간 범위
        
        if not resource_id:
            return jsonify({"error": "resourceId is required"}), 400
        
        # 로그 필터 개선
        # Agent Engine 로그는 여러 리소스 타입에서 올 수 있음
        # datetime.utcnow() 대신 timezone-aware datetime 사용
        from datetime import timezone
        time_filter = (datetime.now(timezone.utc) - timedelta(minutes=minutes)).isoformat()
        
        # 여러 리소스 타입에서 로그 조회
        filter_strs = [
            # Reasoning Engine 직접 로그
            f'resource.type="aiplatform.googleapis.com/ReasoningEngine" AND resource.labels.reasoning_engine_id="{resource_id}" AND timestamp>="{time_filter}"',
            # Vertex AI 일반 로그 (Agent Engine 관련)
            f'resource.type="aiplatform.googleapis.com/ReasoningEngine" AND jsonPayload.message=~".*{resource_id}.*" AND timestamp>="{time_filter}"',
            # Cloud Run 로그 (Agent Engine이 Cloud Run에서 실행되는 경우)
            f'resource.type="cloud_run_revision" AND jsonPayload.message=~".*{resource_id}.*" AND timestamp>="{time_filter}"',
        ]
        
        all_logs = []
        seen_messages = set()  # 중복 제거
        
        for filter_str in filter_strs:
            try:
                entries = logging_client.list_entries(
                    filter_=filter_str,
                    max_results=limit,
                    order_by=logging_v2.DESCENDING,
                )
                
                for entry in entries:
                    # 로그 메시지 생성
                    if isinstance(entry.payload, dict):
                        message = entry.payload.get("message", "")
                        if not message:
                            message = entry.payload.get("textPayload", "")
                        if not message:
                            message = json.dumps(entry.payload, ensure_ascii=False)
                    elif isinstance(entry.payload, str):
                        message = entry.payload
                    else:
                        message = str(entry.payload)
                    
                    # 중복 체크 (메시지 + 타임스탬프)
                    log_key = f"{entry.timestamp}_{message[:100]}"
                    if log_key in seen_messages:
                        continue
                    seen_messages.add(log_key)
                    
                    # 심각도 결정
                    severity = "info"
                    if entry.severity:
                        # severity가 객체인 경우
                        if hasattr(entry.severity, 'name'):
                            severity = entry.severity.name.lower()
                        # severity가 문자열인 경우
                        elif isinstance(entry.severity, str):
                            severity = entry.severity.lower()
                    
                    # 메시지에서 레벨 추출 시도
                    if isinstance(entry.payload, dict):
                        if "severity" in entry.payload:
                            severity = entry.payload["severity"].lower()
                        elif "level" in entry.payload:
                            severity = entry.payload["level"].lower()
                    
                    log_data = {
                        "timestamp": entry.timestamp.isoformat() if entry.timestamp else None,
                        "level": severity,
                        "message": message,
                        "resource_type": entry.resource.type if hasattr(entry, 'resource') else "unknown",
                    }
                    
                    all_logs.append(log_data)
            except Exception as e:
                # 429 에러는 조용히 처리 (너무 자주 로깅하지 않음)
                error_str = str(e)
                if "429" in error_str or "RATE_LIMIT_EXCEEDED" in error_str or "Quota exceeded" in error_str:
                    # 429 에러는 로깅하지 않고 조용히 건너뜀
                    continue
                # 필터 실패해도 계속 진행
                print(f"로그 필터 오류: {e}", file=sys.stderr)
                continue
        
        # 타임스탬프로 정렬
        all_logs.sort(key=lambda x: x["timestamp"] or "", reverse=True)
        
        # 제한 적용
        return jsonify(all_logs[:limit])
        
    except Exception as e:
        import traceback
        return jsonify({
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    print("=" * 50)
    print("Travel Concierge Chat UI Server")
    print("=" * 50)
    print(f"Project: {PROJECT_ID}")
    print(f"Location: {LOCATION}")
    print(f"")
    print(f"서버가 시작되었습니다!")
    print(f"브라우저에서 다음 URL을 열어주세요:")
    print(f"  http://localhost:{port}")
    print(f"")
    print("서버 종료: Ctrl+C")
    print("=" * 50)
    app.run(host="0.0.0.0", port=port, debug=True)
