#ifndef _HID_CAL_H_
#define _HID_CAL_H_

#ifdef LIBHID_EXPORTS
#define LIBHID_API __declspec(dllexport)
#else
#define LIBHID_API __declspec(dllimport)
#endif

#include <windows.h>

#define PACKET_SIZE 65

class LIBHID_API CPrtHID
{
  public:
	CPrtHID ( void );
	~CPrtHID ( void );

  public:

	BOOL HID_Detect ( void );
	BOOL HID_Connect ( void );
	void HID_Disconnect ( void );
	BOOL HID_IsConncet ( void );
	BOOL HID_Read ( UINT8* outbuffer, UINT16 length = PACKET_SIZE );
	BOOL HID_Write ( UINT8* inbuffer, UINT16 length = PACKET_SIZE );


  private:	

	HANDLE m_portHandle;
	char m_devicePath[260];

};


extern "C"
{

	LIBHID_API BOOL HID_Init ( void );
	LIBHID_API void HID_Destory ( void );
	LIBHID_API BOOL HID_Detect ( void );
	LIBHID_API BOOL HID_Connect ( void );
	LIBHID_API void HID_Disconnect ( void );
	LIBHID_API BOOL HID_IsConncet ( void );
	LIBHID_API BOOL HID_Read ( UINT8* outbuffer, UINT16 length = PACKET_SIZE );
	LIBHID_API BOOL HID_Write ( UINT8* inbuffer, UINT16 length = PACKET_SIZE );

}
#undef LIBHID_API

#endif


