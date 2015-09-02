from vt_manager.communication.sfa.rspecs.elements.element import Element
 
class Channel(Element):
    
    fields = [
        'reservation_id',
        'channel_num',
        'frequency',
        'standard',
        'slice_id',
        'start_time',
        'duration',
    ]
