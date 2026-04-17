import { useEffect, useState } from 'react';
import { TexthookerClientSettings } from '../../settings';
import { TexthookerClient } from '../../texthooker-client/texthooker-client';


export const useTexthookerClient = ({ settings }: { settings: TexthookerClientSettings }) => {
    const [client, setClient] = useState<TexthookerClient>();

    useEffect(() => {
        if (settings.texthookerBroadcastEnabled && settings.texthookerServerUrl) {
            const c = new TexthookerClient();
            c.connect(settings.texthookerServerUrl).catch(console.error);
            setClient(c);
            return () => c.disconnect();
        }

        setClient(undefined);
    }, [settings.texthookerBroadcastEnabled, settings.texthookerServerUrl]);

    return client;
};