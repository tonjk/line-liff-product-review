exports.handler = async function () {
    return {
        statusCode: 200,
        body: JSON.stringify({ LIFF_ID: process.env.LIFF_ID }), // Securely fetch LIFF_ID
    };
};
