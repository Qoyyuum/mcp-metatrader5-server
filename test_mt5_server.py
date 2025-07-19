#!/usr/bin/env python3
"""
Comprehensive test for MT5 MCP Server running on VPS.
Tests all server functionality including MCP protocol and MT5 tools.
"""

import requests
import json
import os
from typing import Dict, Any, Optional

class MT5ServerTester:
    """Test client for MT5 MCP Server."""
    
    def __init__(self, server_url: str = "http://31.220.101.24:8000"):
        self.base_url = server_url
        self.mcp_url = f"{server_url}/mt5/mcp/"
        self.sse_url = f"{server_url}/"  # SSE endpoint at root
        self.session = requests.Session()
        self.session_id = None
        # FastMCP streamable HTTP headers
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        })
        
    def parse_sse_response(self, sse_text: str) -> Dict[str, Any]:
        """Parse Server-Sent Events response format."""
        try:
            # SSE format: "event: message\ndata: {json}\n\n"
            lines = sse_text.strip().split('\n')
            data_line = None
            
            for line in lines:
                if line.startswith('data: '):
                    data_line = line[6:]  # Remove 'data: ' prefix
                    break
            
            if data_line:
                return json.loads(data_line)
            else:
                return {"error": "No data found in SSE response"}
                
        except Exception as e:
            return {"error": f"Failed to parse SSE: {e}"}
    
    def establish_session(self) -> bool:
        """Establish a session with the FastMCP server."""
        try:
            # Make initial request to establish session
            message = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "mt5-test-client",
                        "version": "1.0.0"
                    }
                }
            }
            
            # Make the initial request and capture all response details
            response = self.session.post(
                self.mcp_url,
                json=message,
                timeout=10
            )
            
            print(f"   Session establishment: {response.status_code}")
            print(f"   Response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                # Extract session ID from headers
                session_id = response.headers.get('mcp-session-id')
                if session_id:
                    self.session_id = session_id
                    # Add session ID to all future requests
                    self.session.headers.update({
                        "mcp-session-id": session_id
                    })
                    print(f"   Session ID captured: {session_id}")
                
                # Parse SSE response to get the session info
                if response.text.strip():
                    result = self.parse_sse_response(response.text)
                    print(f"   Initialize result: {result.get('result', {}).get('protocolVersion', 'Unknown')}")
                    
                    if 'result' in result:
                        print("✅ MCP protocol handshake successful")
                        self._initialized = True
                        
                        # Test if session is working by making a simple call
                        try:
                            test_response = self.session.post(
                                self.mcp_url,
                                json={
                                    "jsonrpc": "2.0",
                                    "id": 2,
                                    "method": "tools/list",
                                    "params": {}
                                },
                                timeout=5
                            )
                            print(f"   Session test call: {test_response.status_code}")
                            if test_response.status_code == 200:
                                print("✅ Session persistence confirmed")
                                return True
                            else:
                                print(f"   Session test failed: {test_response.text[:200]}")
                        except Exception as e:
                            print(f"   Session test error: {e}")
                        
                        return True
                    else:
                        print(f"❌ MCP handshake failed: {result}")
                        return False
                else:
                    print("   Empty response")
                    return False
            else:
                print(f"   Session establishment failed: {response.text}")
                return False
                
        except Exception as e:
            print(f"   Session establishment error: {e}")
            return False
    
    def mcp_call_with_session(self, method: str, params: Optional[Dict[str, Any]] = None, timeout: int = 10) -> Dict[str, Any]:
        """Make an MCP call using the established session."""
        
        # Check if we have an initialized session
        if not getattr(self, '_initialized', False):
            raise Exception("Session not initialized. Call establish_session() first.")
        
        message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params or {}
        }
        
        # Use the same session and URL - FastMCP should maintain session via HTTP connection
        response = self.session.post(
            self.mcp_url,
            json=message,
            timeout=timeout
        )
        
        print(f"   MCP call: {response.status_code}")
        
        if response.status_code == 200:
            if response.text.strip():
                result = self.parse_sse_response(response.text)
                return result
            else:
                return {"result": {"success": True}}
        else:
            error_text = response.text[:500] if response.text else "No response body"
            print(f"   Error response: {error_text}")
            raise Exception(f"HTTP {response.status_code}: {error_text}")
    
    def mcp_call(self, method: str, params: Optional[Dict[str, Any]] = None, timeout: int = 10) -> Dict[str, Any]:
        """Make an MCP JSON-RPC call using the best available transport."""
        
        # Use SSE endpoint if it's working
        if getattr(self, '_sse_working', False):
            return self.mcp_call_sse(method, params, timeout)
        else:
            return self.mcp_call_with_session(method, params, timeout)
    
    def mcp_call_sse(self, method: str, params: Optional[Dict[str, Any]] = None, timeout: int = 10) -> Dict[str, Any]:
        """Make an MCP call using the SSE endpoint."""
        message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params or {}
        }
        
        response = self.session.post(
            self.sse_url,
            json=message,
            timeout=timeout
        )
        
        print(f"   SSE MCP call: {response.status_code}")
        
        if response.status_code == 200:
            if response.text.strip():
                return self.parse_sse_response(response.text)
            else:
                return {"result": {"success": True}}
        else:
            error_text = response.text[:500] if response.text else "No response body"
            raise Exception(f"HTTP {response.status_code}: {error_text}")
    
    def test_connectivity(self) -> bool:
        """Test basic server connectivity."""
        print("🔍 Testing server connectivity...")
        
        try:
            # Test root endpoint
            response = self.session.get(self.base_url, timeout=5)
            print(f"✅ Root endpoint: {response.status_code} - {response.text[:100]}")
            
            # Test different possible endpoints
            endpoints_to_test = [
                ("/mt5", "MT5 HTTP endpoint"),
                ("/docs", "API docs"),
                ("/openapi.json", "OpenAPI spec")
            ]
            
            for endpoint, description in endpoints_to_test:
                try:
                    url = f"{self.base_url}{endpoint}"
                    response = self.session.get(url, timeout=5)
                    print(f"✅ {description}: {response.status_code}")
                except Exception as e:
                    print(f"❌ {description}: {e}")
            
            return True
            
        except requests.exceptions.ConnectionError:
            print("❌ Cannot connect to server - is it running?")
            return False
        except requests.exceptions.Timeout:
            print("❌ Server timeout")
            return False
        except Exception as e:
            print(f"❌ Connectivity error: {e}")
            return False
    
    def test_sse_endpoint(self) -> bool:
        """Test the SSE endpoint which might be easier to work with."""
        print("\n📡 Testing SSE endpoint...")
        
        try:
            # Try the SSE endpoint for MCP calls
            message = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "mt5-test-client",
                        "version": "1.0.0"
                    }
                }
            }
            
            response = self.session.post(
                self.sse_url,
                json=message,
                timeout=10
            )
            
            print(f"   SSE endpoint: {response.status_code}")
            
            if response.status_code == 200:
                # Extract session ID from headers for SSE endpoint too
                session_id = response.headers.get('mcp-session-id')
                if session_id:
                    self.session_id = session_id
                    self.session.headers.update({
                        "mcp-session-id": session_id
                    })
                    print(f"   SSE Session ID captured: {session_id}")
                
                if response.text.strip():
                    result = self.parse_sse_response(response.text)
                    print(f"   SSE result: {result.get('result', {}).get('protocolVersion', 'Unknown')}")
                    
                    if 'result' in result:
                        print("✅ SSE endpoint working")
                        self._sse_working = True
                        return True
                
            print(f"❌ SSE endpoint failed: {response.text[:200]}")
            return False
            
        except Exception as e:
            print(f"❌ SSE endpoint error: {e}")
            return False
    
    def test_mcp_initialize(self) -> bool:
        """Test MCP initialization with session establishment."""
        print("\n🚀 Testing MCP initialization...")
        
        # Try SSE endpoint first
        if self.test_sse_endpoint():
            return True
        
        # Fall back to streamable HTTP
        if not self.establish_session():
            print("❌ Failed to establish session")
            return False
        
        print("✅ MCP session established successfully")
        return True
    
    def test_list_tools(self) -> bool:
        """Test listing available tools."""
        print("\n🔧 Testing tools list...")
        
        try:
            result = self.mcp_call("tools/list")
            
            if "result" in result and "tools" in result["result"]:
                tools = result["result"]["tools"]
                print(f"✅ Found {len(tools)} tools:")
                
                for tool in tools:
                    name = tool.get("name", "Unknown")
                    desc = tool.get("description", "No description")
                    print(f"   • {name}: {desc}")
                
                return len(tools) > 0
            elif "error" in result:
                print(f"❌ Tools list failed with error: {result['error']}")
                return False
            else:
                print(f"❌ Tools list failed: {result}")
                return False
                
        except Exception as e:
            print(f"❌ Tools list error: {e}")
            return False
    
    def test_mt5_tools(self) -> bool:
        """Test specific MT5 tools."""
        print("\n🎯 Testing MT5 tools...")
        
        success_count = 0
        total_tests = 0
        
        # Test server health first
        try:
            total_tests += 1
            result = self.mcp_call("tools/call", {
                "name": "test_server",
                "arguments": {}
            })
            
            if "result" in result:
                print("✅ Server test tool works")
                success_count += 1
                # Show server info
                try:
                    content = result["result"]["content"][0]["text"]
                    print(f"   Server info: {content}")
                except:
                    print(f"   Server response: {result['result']}")
            elif "error" in result:
                print(f"❌ Server test failed with error: {result['error']}")
            else:
                print(f"❌ Server test failed: {result}")
                
        except Exception as e:
            print(f"❌ Server test error: {e}")

        # Test initialize tool
        try:
            total_tests += 1
            result = self.mcp_call("tools/call", {
                "name": "initialize",
                "arguments": {}
            })
            
            if "result" in result:
                print("✅ MT5 initialize tool works")
                success_count += 1
                # Show result details
                try:
                    content = result["result"]["content"][0]["text"]
                    print(f"   Initialize result: {content}")
                except:
                    print(f"   Initialize response: {result['result']}")
            elif "error" in result:
                print(f"❌ MT5 initialize failed with error: {result['error']}")
            else:
                print(f"❌ MT5 initialize failed: {result}")
                
        except Exception as e:
            print(f"❌ MT5 initialize error: {e}")
        
        # Test get_version tool
        try:
            total_tests += 1
            result = self.mcp_call("tools/call", {
                "name": "get_version",
                "arguments": {}
            })
            
            if "result" in result:
                print("✅ MT5 version tool works")
                success_count += 1
                try:
                    content = result["result"]["content"][0]["text"]
                    print(f"   Version info: {content}")
                except:
                    print(f"   Version response: {result['result']}")
            elif "error" in result:
                print(f"❌ MT5 version failed with error: {result['error']}")
            else:
                print(f"❌ MT5 version failed: {result}")
                
        except Exception as e:
            print(f"❌ MT5 version error: {e}")
        
        # Test get_terminal_info tool
        try:
            total_tests += 1
            result = self.mcp_call("tools/call", {
                "name": "get_terminal_info",
                "arguments": {}
            })
            
            if "result" in result:
                print("✅ MT5 terminal info tool works")
                success_count += 1
            elif "error" in result:
                print(f"❌ MT5 terminal info failed with error: {result['error']}")
            else:
                print(f"❌ MT5 terminal info failed: {result}")
                
        except Exception as e:
            print(f"❌ MT5 terminal info error: {e}")
        
        print(f"\n📊 MT5 Tools Test Results: {success_count}/{total_tests} passed")
        return success_count > 0
    
    def test_fastmcp_transport(self) -> bool:
        """Test FastMCP streamable HTTP transport protocol."""
        print("\n🚀 Testing FastMCP streamable HTTP transport...")
        
        try:
            # First, try to establish a session
            endpoint = f"{self.base_url}/mt5/mcp/"
            
            # Try different content types that FastMCP might expect
            content_types = [
                "application/json",
                "application/vnd.mcp+json", 
                "text/plain"
            ]
            
            for content_type in content_types:
                try:
                    headers = {
                        "Content-Type": content_type,
                        "Accept": "application/json, text/event-stream",
                        "Connection": "keep-alive"
                    }
                    
                    # Simple initialize message
                    message = {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "initialize",
                        "params": {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {},
                            "clientInfo": {
                                "name": "mt5-test-client",
                                "version": "1.0.0"
                            }
                        }
                    }
                    
                    response = self.session.post(
                        endpoint,
                        json=message,
                        headers=headers,
                        timeout=10
                    )
                    
                    print(f"   Content-Type {content_type}: {response.status_code}")
                    
                    if response.status_code == 200:
                        # Handle both JSON and SSE responses
                        if response.text.strip():
                            try:
                                # Try parsing as JSON first
                                result = response.json()
                            except:
                                # Fall back to SSE parsing
                                result = self.parse_sse_response(response.text)
                            
                            print(f"✅ FastMCP transport working with {content_type}")
                            print(f"   Response: {result}")
                            
                            # Extract session ID if present
                            session_id = response.headers.get('mcp-session-id')
                            if session_id:
                                self.session_id = session_id
                                self.session.headers.update({
                                    "mcp-session-id": session_id
                                })
                                print(f"   Session ID captured: {session_id}")
                            
                            return True
                    elif response.status_code != 406:
                        print(f"   Response body: {response.text[:200]}")
                        
                except Exception as e:
                    print(f"   Error with {content_type}: {e}")
                    
            return False
            
        except Exception as e:
            print(f"❌ FastMCP transport test failed: {e}")
            return False
    
    def test_server_info(self) -> bool:
        """Get basic server information."""
        print("\n📋 Testing server info endpoints...")
        
        # Test various info endpoints
        info_endpoints = [
            ("/docs", "API Documentation"),
            ("/openapi.json", "OpenAPI Specification"),
            ("/health", "Health Check"),
            ("/info", "Server Info"),
            ("/mt5/docs", "MT5 Documentation"),
            ("/mt5/health", "MT5 Health Check")
        ]
        
        success_count = 0
        for endpoint, description in info_endpoints:
            try:
                url = f"{self.base_url}{endpoint}"
                response = self.session.get(url, timeout=5)
                
                if response.status_code == 200:
                    print(f"✅ {description}: Available")
                    success_count += 1
                    # Show a snippet of the response for docs
                    if "docs" in endpoint or "openapi" in endpoint:
                        content = response.text[:100].replace('\n', ' ')
                        print(f"   Content preview: {content}...")
                elif response.status_code == 404:
                    print(f"❌ {description}: Not found")
                else:
                    print(f"⚠️  {description}: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ {description}: {e}")
        
        return success_count > 0
    
    def run_all_tests(self) -> bool:
        """Run all tests and return overall success."""
        print("🧪 Starting MT5 MCP Server Tests")
        print(f"🌐 Server URL: {self.base_url}")
        print("=" * 50)
        
        tests_passed = 0
        total_tests = 6
        
        # Run tests in order of complexity
        if self.test_connectivity():
            tests_passed += 1
            
        if self.test_server_info():
            tests_passed += 1
            
        if self.test_fastmcp_transport():
            tests_passed += 1
            
        if self.test_mcp_initialize():
            tests_passed += 1
            
        if self.test_list_tools():
            tests_passed += 1
            
        if self.test_mt5_tools():
            tests_passed += 1
        
        # Summary
        print("\n" + "=" * 50)
        print(f"📋 Test Summary: {tests_passed}/{total_tests} test suites passed")
        
        if tests_passed == total_tests:
            print("🎉 All tests passed! Server is working correctly.")
            return True
        elif tests_passed > 0:
            print("⚠️  Some tests passed. Server is partially functional.")
            return True
        else:
            print("❌ All tests failed. Server may not be working.")
            return False

def main():
    """Main test function."""
    # Get server URL from environment or use default
    server_url = os.getenv("MT5_MCP_SERVER_URL", "http://31.220.101.24:8000")
    if server_url.endswith("/mt5/mcp"):
        server_url = server_url.replace("/mt5/mcp", "")
    
    # Run tests
    tester = MT5ServerTester(server_url)
    success = tester.run_all_tests()
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())