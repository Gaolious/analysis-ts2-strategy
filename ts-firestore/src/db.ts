import { initializeApp} from "firebase/app";
import {getAuth, signInWithCustomToken} from "firebase/auth";
import {collection, doc, getDoc, getDocs, getFirestore, limit, query } from "firebase/firestore";
import {getDocFromServer, getDocsFromServer} from "@firebase/firestore";

export async function getJobs(token: string, guildId: string, firebaseConfig: { [key: string]: string }): Promise<string> {
    const app = initializeApp(firebaseConfig);
    const auth = getAuth(app);

    console.log(`# 4. let userCredential = await signInWithCustomToken(auth, token)`)
    let userCredential = await signInWithCustomToken(auth, token)
    const user = userCredential.user;
    const path = `env/prod/guilds/${guildId}/jobs`;

    console.log(`# 5. const db = getFirestore(app);`)
    const db = getFirestore(app);
    const usersCollectionRef = collection(db, path);
    const q = query(
        usersCollectionRef,
        limit(10)
    );

    console.log(`# 6. data = await getDocs(q);`)
    const querySnapshot = await getDocsFromServer(q)
    const newData = querySnapshot.docs.map(doc => ({...doc.data()}))
    return JSON.stringify(newData);
}


